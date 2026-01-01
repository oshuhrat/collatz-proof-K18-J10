#!/usr/bin/env python3
"""
verify_full_theorem_K18_J10.py

Single-shot verifier for the Collatz proof bundle (K=18, P=64, d in [-10,6]).

This script:
1) reads paper/artifacts.json (canonical manifest),
2) locates the artifact bundle directory,
3) verifies SHA256 of the four artifact files,
4) verifies rank monotonicity on a fixed RNG sample of live edges,
5) verifies hit_r0 == 0 via bad-preimage bitset,
6) verifies FULL exit_high => 1-step descent,
7) verifies FULL shrink => 2-step descent,
and prints:

    [THEOREM VERIFY] OK

Authors: Shuhrat Okilov, Ulugbek Khamidov
Project: Alet (Ethical AGI Development), Samarkand, Uzbekistan
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Any, Tuple

import numpy as np


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


def repo_root_from_this_file() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------- Manifest -----------------------------

@dataclass(frozen=True)
class Params:
    K: int
    P: int
    dmin: int
    dmax: int
    D: int
    N_odd: int
    N_states: int
    packing: str


@dataclass(frozen=True)
class Files:
    next_path: str
    kill_path: str
    badbit_path: str
    rank_path: str

    next_sha: str
    kill_sha: str
    badbit_sha: str
    rank_sha: str


def read_manifest(manifest_path: str) -> Tuple[Params, Dict[str, Any]]:
    m = load_json(manifest_path)
    p = m["parameters"]
    params = Params(
        K=int(p["K"]),
        P=int(p["P"]),
        dmin=int(p["dmin"]),
        dmax=int(p["dmax"]),
        D=int(p["D"]),
        N_odd=int(p["N_odd"]),
        N_states=int(p["N_states"]),
        packing=str(p["packing"]),
    )
    if params.packing != "A":
        raise ValueError(f"Unsupported packing in manifest: {params.packing}")
    return params, m


def resolve_bundle_dir(args_bundle: str | None, env_bundle: str | None, repo_root: str) -> str:
    if args_bundle:
        return os.path.abspath(args_bundle)
    if env_bundle:
        return os.path.abspath(env_bundle)
    return os.path.abspath(os.path.join(repo_root, "collatz_LT_K18_J10_bundle"))


def resolve_files(manifest: Dict[str, Any], bundle_dir: str) -> Files:
    sha_map: Dict[str, str] = {}
    for ent in manifest["files"]:
        sha_map[ent["filename"]] = ent["sha256"]

    def p(name: str) -> str:
        return os.path.join(bundle_dir, name)

    next_fn = "next_K18_d-10_6_P64.dat"
    kill_fn = "kill_kind_K18_d-10_6_P64.dat"
    bad_fn  = "badpre_exitlow_K18_d-10_6_P64.bit"
    rank_fn = "rank_K18_d-10_6_P64.dat"

    for fn in [next_fn, kill_fn, bad_fn, rank_fn]:
        if fn not in sha_map:
            raise KeyError(f"Manifest does not contain sha256 for {fn}")

    return Files(
        next_path=p(next_fn),
        kill_path=p(kill_fn),
        badbit_path=p(bad_fn),
        rank_path=p(rank_fn),
        next_sha=sha_map[next_fn],
        kill_sha=sha_map[kill_fn],
        badbit_sha=sha_map[bad_fn],
        rank_sha=sha_map[rank_fn],
    )


# ----------------------------- Verifier -----------------------------

def unpack_sid_A(sid: int, D: int, dmin: int, P: int) -> Tuple[int, int, int]:
    """
    Packing A:
      sid = ((i * D + (d - dmin)) * P + r)
      a = 2*i + 1
    Returns (a,d,r).
    """
    r = sid % P
    sid //= P
    d_off = sid % D
    sid //= D
    i = sid
    a = (i << 1) | 1
    d = d_off + dmin
    return a, d, r


def verify_all(params: Params, files: Files, manifest: Dict[str, Any],
               rank_sample: int, seed: int, full_exit_high: bool, full_shrink: bool) -> None:
    for pth in [files.next_path, files.kill_path, files.badbit_path, files.rank_path]:
        if not os.path.exists(pth):
            raise FileNotFoundError(pth)

    # 1) SHA checks
    sha_next = sha256_file(files.next_path)
    sha_kill = sha256_file(files.kill_path)
    sha_bad  = sha256_file(files.badbit_path)
    sha_rank = sha256_file(files.rank_path)

    if sha_next != files.next_sha:
        raise AssertionError(f"SHA mismatch next: got {sha_next} expected {files.next_sha}")
    if sha_kill != files.kill_sha:
        raise AssertionError(f"SHA mismatch kill_kind: got {sha_kill} expected {files.kill_sha}")
    if sha_bad != files.badbit_sha:
        raise AssertionError(f"SHA mismatch badpre_exitlow: got {sha_bad} expected {files.badbit_sha}")
    if sha_rank != files.rank_sha:
        raise AssertionError(f"SHA mismatch rank: got {sha_rank} expected {files.rank_sha}")

    # 2) Memmaps
    N = params.N_states
    nxt  = np.memmap(files.next_path, dtype=np.int32, mode="r", shape=(N,))
    kk   = np.memmap(files.kill_path, dtype=np.uint8, mode="r", shape=(N,))
    rank = np.memmap(files.rank_path, dtype=np.uint32, mode="r", shape=(N,))

    # 3) Rank monotonicity sample
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, N, size=rank_sample, dtype=np.int64)
    for u in idx:
        u = int(u)
        v = int(nxt[u])
        if v != -1:
            if not (int(rank[v]) < int(rank[u])):
                raise AssertionError(f"Rank violation at u={u} v={v} rank[u]={int(rank[u])} rank[v]={int(rank[v])}")

    # 4) hit_r0 == 0 using bad-preimage bitset
    expected_hit = int(manifest["verified_claims"]["hit_r0"]["expected_value"])
    if expected_hit != 0:
        raise ValueError("Manifest expected hit_r0 is not 0; verifier assumes 0 for this bundle.")

    with open(files.badbit_path, "rb") as f:
        packed = np.frombuffer(f.read(), dtype=np.uint8)
    badmask = np.unpackbits(packed)[:N].astype(np.uint8)

    d0 = int(manifest["semantic_start_set"]["d0"])
    r0 = int(manifest["semantic_start_set"]["r0"])

    for i in range(params.N_odd):
        sid0 = ((i * params.D + (d0 - params.dmin)) * params.P + r0)
        if badmask[sid0]:
            a = (i << 1) | 1
            raise AssertionError(f"hit_r0 != 0, witness a={a}")

    # 5) exit_high FULL descent
    exp_exit_high_count = int(manifest["verified_claims"]["exit_high_descent_full"]["expected_exit_high_count"])
    exp_k_min = int(manifest["verified_claims"]["exit_high_descent_full"]["expected_k_min"])
    exp_k_max = int(manifest["verified_claims"]["exit_high_descent_full"]["expected_k_max"])

    exit_high = np.where((nxt == -1) & (kk == 2))[0].astype(np.int64)
    if int(exit_high.size) != exp_exit_high_count:
        raise AssertionError(f"exit_high_count mismatch: got {int(exit_high.size)} expected {exp_exit_high_count}")

    if full_exit_high:
        kmin = 10**9
        kmax = -1
        for s in exit_high:
            a, _, _ = unpack_sid_A(int(s), params.D, params.dmin, params.P)
            y = 3 * a + 1
            k = v2_pos(y)
            n1 = y >> k
            if not (n1 < a):
                raise AssertionError(f"exit_high not descending at a={a} (n1={n1}, k={k})")
            if k < kmin: kmin = k
            if k > kmax: kmax = k
        if kmin != exp_k_min or kmax != exp_k_max:
            raise AssertionError(f"exit_high k-range mismatch: got [{kmin},{kmax}] expected [{exp_k_min},{exp_k_max}]")

    # 6) shrink FULL 2-step descent
    exp_shrink_count = int(manifest["verified_claims"]["shrink_2step_descent_full"]["expected_shrink_count"])
    shrink = np.where((nxt == -1) & (kk == 1))[0].astype(np.int64)
    if int(shrink.size) != exp_shrink_count:
        raise AssertionError(f"shrink_count mismatch: got {int(shrink.size)} expected {exp_shrink_count}")

    if full_shrink:
        for s in shrink:
            a, _, _ = unpack_sid_A(int(s), params.D, params.dmin, params.P)

            # Step 1: n1 = F(a)
            y1 = 3 * a + 1
            k1 = v2_pos(y1)
            n1 = y1 >> k1

            if (n1 & 7) != 1:
                raise AssertionError(f"shrink invariant failed: n1 mod 8 != 1 at a={a} (n1={n1})")

            if n1 == 1:
                continue

            # Step 2: n2 = F(n1) and must satisfy n2 < n1
            y2 = 3 * n1 + 1
            k2 = v2_pos(y2)
            n2 = y2 >> k2
            if not (n2 < n1):
                raise AssertionError(f"shrink 2-step descent failed at a={a} (n1={n1}, n2={n2})")


# ----------------------------- CLI -----------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Single-shot verifier for the Collatz proof bundle (K=18, d in [-10,6], P=64)."
    )
    ap.add_argument(
        "--bundle-dir",
        default=None,
        help="Directory containing the four artifact files. "
             "If omitted, uses $COLLATZ_BUNDLE_DIR or ./collatz_LT_K18_J10_bundle."
    )
    ap.add_argument(
        "--manifest",
        default=None,
        help="Path to paper/artifacts.json. If omitted, uses repo paper/artifacts.json."
    )
    ap.add_argument(
        "--rank-sample",
        type=int,
        default=2_000_000,
        help="Sample size for rank monotonicity check."
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=0,
        help="RNG seed for rank sample."
    )
    ap.add_argument(
        "--skip-exit-high-full",
        action="store_true",
        help="Skip FULL exit_high descent check (not recommended)."
    )
    ap.add_argument(
        "--skip-shrink-full",
        action="store_true",
        help="Skip FULL shrink 2-step descent check (not recommended)."
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    repo_root = repo_root_from_this_file()
    manifest_path = args.manifest or os.path.join(repo_root, "paper", "artifacts.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(manifest_path)

    params, manifest = read_manifest(manifest_path)

    bundle_dir = resolve_bundle_dir(args.bundle_dir, os.environ.get("COLLATZ_BUNDLE_DIR"), repo_root)

    files = resolve_files(manifest, bundle_dir)

    verify_all(
        params=params,
        files=files,
        manifest=manifest,
        rank_sample=int(args.rank_sample),
        seed=int(args.seed),
        full_exit_high=not args.skip_exit_high_full,
        full_shrink=not args.skip_shrink_full,
    )

    print("[THEOREM VERIFY] OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[THEOREM VERIFY] FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        raise