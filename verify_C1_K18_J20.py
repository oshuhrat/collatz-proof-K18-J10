#!/usr/bin/env python3
"""
scripts/verify_C1_K18_J20.py

One-shot verifier for the FINAL C1 bundle (K=18, P=64, J=20, d in [-20,6]) with delta_P64.

Accepts either:
  --bundle /path/to/unzipped_dir
or
  --bundle /path/to/bundle_C1_K18_J20_FINAL.zip   (auto-extracts to a temp dir)

Checks:
(V1) SHA256 + file sizes,
(V1') semantic recomputation consistency on a random sample (default 2,000,000),
(V4) all starts (a,0,0) are in goodpre,
(V2) rank monotonicity on live edges restricted to goodpre,
(V5) witness checks at progress kills (carry/exit_high/shrink2),
(V3) optional full recomputation of goodpre (RAM-heavy) if --heavy-goodpre is set.

Prints exactly:
  [THEOREM VERIFY] OK

Authors: Shuhrat Okilov, Ulugbek Khamidov
Project: Alet (Ethical AI Development), Samarkand, Uzbekistan
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from collections import deque
from dataclasses import dataclass
from typing import Dict, Any, Tuple

import numpy as np

# -------------------- Fixed parameters for C1 J=20 --------------------

K = 18
P = 64
J = 20
DMIN = -20
DMAX = 6
D = 27
A = 1 << (K - 1)  # 131072
N = A * D * P     # 226,492,416
MASK = (1 << K) - 1

LIVE = 0
SHRINK2 = 1
EXIT_HIGH = 2
EXIT_LOW = 3
CARRY = 4

GOOD_KINDS = {SHRINK2, EXIT_HIGH, CARRY}


# ----------------------------- Utilities -----------------------------

def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def v2_pos(x: int) -> int:
    """2-adic valuation for positive integer x."""
    c = 0
    while (x & 1) == 0:
        x >>= 1
        c += 1
    return c


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def unpackbits_file(path: str, nbits: int) -> np.ndarray:
    packed = np.fromfile(path, dtype=np.uint8)
    bits = np.unpackbits(packed)[:nbits].astype(np.uint8)
    return bits


def unpack_sid_A(sid: int) -> Tuple[int, int, int, int]:
    """
    Packing A with D=27, dmin=-20:
      sid = ((i * D + (d - dmin)) * P + r), a = 2*i+1
    Returns (a, i, d, r).
    """
    r = sid % P
    q = sid // P
    j = q % D
    i = q // D
    a = (i << 1) | 1
    d = DMIN + j
    return a, i, d, r


def sid_pack(i: int, d: int, r: int) -> int:
    j = d - DMIN
    return ((i * D + j) * P + r)


def resolve_bundle_dir(bundle: str) -> str:
    bundle = os.path.abspath(bundle)
    if os.path.isdir(bundle):
        return bundle
    if os.path.isfile(bundle) and bundle.lower().endswith(".zip"):
        td = tempfile.mkdtemp(prefix="c1j20_bundle_")
        with zipfile.ZipFile(bundle, "r") as z:
            z.extractall(td)
        return td
    raise FileNotFoundError(bundle)


# ----------------------------- Semantic recomputation -----------------------------

def classify_and_next(a: int, d: int, r: int, delta: np.ndarray) -> Tuple[int, int, int, int, int]:
    """
    Returns (kind, next_or_-1, k, a1, dprime).
    Priority: carry, shrink2, exit_high, exit_low, live.
    """
    y = 3 * a + 1
    k = v2_pos(y)
    a1 = y >> k  # odd
    dprime = d + k - int(delta[r])
    rprime = (r + 1) & 63

    if k >= K:
        return CARRY, -1, k, a1, dprime

    if k >= 2 and (a1 & 7) == 1:
        return SHRINK2, -1, k, a1, dprime

    if dprime > DMAX:
        return EXIT_HIGH, -1, k, a1, dprime

    if dprime < DMIN:
        return EXIT_LOW, -1, k, a1, dprime

    aprime = a1 & MASK
    ip = aprime >> 1
    nxt = sid_pack(ip, dprime, rprime)
    return LIVE, nxt, k, a1, dprime


def recompute_goodpre_heavy(kk: np.memmap, nxt: np.memmap) -> np.ndarray:
    """
    Full Pre*(Good) along live edges using in-RAM predecessor arrays.
    RAM-heavy but exact.
    """
    is_live = (kk == LIVE)
    is_good = (kk == SHRINK2) | (kk == EXIT_HIGH) | (kk == CARRY)

    live_u = np.where(is_live)[0].astype(np.int64)
    live_v = nxt[live_u].astype(np.int64)

    indeg = np.zeros(N, dtype=np.int32)
    np.add.at(indeg, live_v, 1)

    offs = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(indeg, out=offs[1:])

    m = int(offs[-1])
    pred_u = np.empty(m, dtype=np.int32)
    cur = offs[:-1].copy()

    for uu, vv in zip(live_u, live_v):
        idx = cur[vv]
        pred_u[idx] = np.int32(uu)
        cur[vv] = idx + 1

    goodpre = np.zeros(N, dtype=np.uint8)
    good_ids = np.where(is_good)[0].astype(np.int64)
    dq = deque(good_ids.tolist())
    for u in dq:
        goodpre[int(u)] = 1

    while dq:
        x = dq.popleft()
        s = int(offs[x]); e = int(offs[x + 1])
        for uu in pred_u[s:e]:
            uui = int(uu)
            if goodpre[uui] == 0:
                goodpre[uui] = 1
                dq.append(uui)

    return goodpre


# ----------------------------- Main verifier -----------------------------

@dataclass(frozen=True)
class Paths:
    delta: str
    kill: str
    nxt: str
    goodpre: str
    rank: str


def resolve_paths(bundle_dir: str) -> Paths:
    return Paths(
        delta=os.path.join(bundle_dir, "delta_P64.dat"),
        kill=os.path.join(bundle_dir, "kill_kind_K18_d-20_6_P64.dat"),
        nxt=os.path.join(bundle_dir, "next_K18_d-20_6_P64.dat"),
        goodpre=os.path.join(bundle_dir, "goodpre_K18_d-20_6_P64.bit"),
        rank=os.path.join(bundle_dir, "rank_K18_d-20_6_P64.dat"),
    )


def verify(bundle: str, artifacts_json: str, sample_v1: int, seed: int, heavy_goodpre: bool) -> None:
    bundle_dir = resolve_bundle_dir(bundle)
    paths = resolve_paths(bundle_dir)

    for p in [paths.delta, paths.kill, paths.nxt, paths.goodpre, paths.rank]:
        if not os.path.exists(p):
            raise FileNotFoundError(p)

    m = load_json(artifacts_json)
    sha_map = {e["filename"]: e["sha256"] for e in m["files"]}

    # (V1) size checks
    if os.path.getsize(paths.delta) != 64:
        raise AssertionError("delta_P64.dat must be 64 bytes")
    if os.path.getsize(paths.kill) != N:
        raise AssertionError("kill_kind size mismatch")
    if os.path.getsize(paths.nxt) != 4 * N:
        raise AssertionError("next size mismatch")
    if os.path.getsize(paths.rank) != 4 * N:
        raise AssertionError("rank size mismatch")
    exp_gp_bytes = (N + 7) // 8
    if os.path.getsize(paths.goodpre) != exp_gp_bytes:
        raise AssertionError("goodpre size mismatch")

    # (V1) SHA checks
    def check_sha(filename: str, path: str):
        got = sha256_file(path)
        exp = sha_map[filename]
        if got != exp:
            raise AssertionError(f"SHA mismatch for {filename}: got {got} expected {exp}")

    check_sha("delta_P64.dat", paths.delta)
    check_sha("kill_kind_K18_d-20_6_P64.dat", paths.kill)
    check_sha("next_K18_d-20_6_P64.dat", paths.nxt)
    check_sha("goodpre_K18_d-20_6_P64.bit", paths.goodpre)
    check_sha("rank_K18_d-20_6_P64.dat", paths.rank)

    # Load core arrays
    delta = np.fromfile(paths.delta, dtype=np.uint8)
    if delta.size != 64 or not np.all((delta == 1) | (delta == 2)):
        raise AssertionError("delta must be 64 uint8 values in {1,2}")

    kk = np.memmap(paths.kill, dtype=np.uint8, mode="r", shape=(N,))
    nxt = np.memmap(paths.nxt, dtype=np.int32, mode="r", shape=(N,))
    rank = np.memmap(paths.rank, dtype=np.uint32, mode="r", shape=(N,))
    goodpre = unpackbits_file(paths.goodpre, N)

    # (V4) start coverage
    j0 = 0 - DMIN  # 20
    for i in range(A):
        sid0 = ((i * D + j0) * P + 0)
        if goodpre[sid0] == 0:
            a = (i << 1) | 1
            raise AssertionError(f"V4 failed: start not in goodpre, a={a}, sid0={sid0}")

    # (V2) rank monotonicity on live edges restricted to goodpre
    live_in_gp = np.where((kk == LIVE) & (goodpre == 1))[0].astype(np.int64)
    v = nxt[live_in_gp].astype(np.int64)

    if not np.all(goodpre[v] == 1):
        bad = int(live_in_gp[np.where(goodpre[v] != 1)[0][0]])
        raise AssertionError(f"V2 scope failed: live edge exits goodpre at sid={bad} v={int(nxt[bad])}")

    ok = rank[v] < rank[live_in_gp]
    if not np.all(ok):
        bad = int(live_in_gp[np.where(~ok)[0][0]])
        raise AssertionError(
            f"V2 rank violation in goodpre: sid={bad}, rank[u]={int(rank[bad])}, "
            f"v={int(nxt[bad])}, rank[v]={int(rank[int(nxt[bad])])}"
        )

    # (V5) witness checks at progress kills (full)
    good_ids = np.where((kk == SHRINK2) | (kk == EXIT_HIGH) | (kk == CARRY))[0].astype(np.int64)
    for sid in good_ids:
        sid = int(sid)
        a, _, d, r = unpack_sid_A(sid)
        kind_file = int(kk[sid])
        kind_rec, _, k, a1, dprime = classify_and_next(a, d, r, delta)
        if kind_file != kind_rec:
            raise AssertionError(f"V1' mismatch at Good sid={sid}: file kind={kind_file} rec kind={kind_rec}")

        if kind_file == CARRY:
            if k < 18:
                raise AssertionError(f"V5 carry witness failed sid={sid} k={k}")
        elif kind_file == EXIT_HIGH:
            if k < 2:
                raise AssertionError(f"V5 exit_high witness failed sid={sid} k={k}")
        elif kind_file == SHRINK2:
            if k < 2 or (a1 & 7) != 1:
                raise AssertionError(f"V5 shrink2 witness failed sid={sid} k={k} a1mod8={a1&7}")
        else:
            raise AssertionError("Unexpected Good kind")

    # (V1') semantic recomputation consistency (sample)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, N, size=sample_v1, dtype=np.int64)
    for sid in idx:
        sid = int(sid)
        a, _, d, r = unpack_sid_A(sid)
        kind_rec, nxt_rec, k, a1, dprime = classify_and_next(a, d, r, delta)

        kind_file = int(kk[sid])
        if kind_file != kind_rec:
            raise AssertionError(f"V1' mismatch at sid={sid}: file kind={kind_file} rec kind={kind_rec}")

        if kind_rec == LIVE:
            if int(nxt[sid]) != nxt_rec:
                raise AssertionError(f"V1' next mismatch at sid={sid}: file next={int(nxt[sid])} rec next={nxt_rec}")
        else:
            if int(nxt[sid]) != -1:
                raise AssertionError(f"V1' expected next=-1 at kill sid={sid}, got {int(nxt[sid])}")

    # (V3) optionally recompute goodpre fully and compare
    if heavy_goodpre:
        gp_rec = recompute_goodpre_heavy(kk, nxt)
        if not np.array_equal(gp_rec, goodpre):
            bad = int(np.where(gp_rec != goodpre)[0][0])
            raise AssertionError(f"V3 goodpre mismatch at sid={bad}: rec={int(gp_rec[bad])} file={int(goodpre[bad])}")

    print("[THEOREM VERIFY] OK")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="One-shot verifier for C1 K=18 J=20 FINAL bundle.")
    ap.add_argument("--bundle", required=True, help="Path to bundle dir or FINAL zip.")
    ap.add_argument("--artifacts-json", default="paper/artifacts_C1_J20.json", help="Path to artifacts_C1_J20.json.")
    ap.add_argument("--sample-v1", type=int, default=2_000_000, help="Sample size for V1' recomputation.")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for sampling.")
    ap.add_argument("--heavy-goodpre", action="store_true", help="Recompute goodpre fully (RAM-heavy).")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    verify(
        bundle=str(args.bundle),
        artifacts_json=str(args.artifacts_json),
        sample_v1=int(args.sample_v1),
        seed=int(args.seed),
        heavy_goodpre=bool(args.heavy_goodpre),
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[THEOREM VERIFY] FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        raise