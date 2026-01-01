Release archive (Zenodo v1.0.0): https://doi.org/10.5281/zenodo.18114235
Concept DOI (all versions): https://doi.org/10.5281/zenodo.18114234
# Reproducibility Guide (K=18, dв€€[-10,6], P=64)

This document describes the **exact reproducibility contract** for the Collatz proof bundle.

---

## 1) Prerequisites

* Python 3.10+ (Windows / Linux / macOS)
* `numpy`

Install:

```bash
pip install numpy
```

---

## 2) Bundle layout

You must have these four files present in a directory:

```text
collatz_LT_K18_J10_bundle/
```

Required filenames:

```text
next_K18_d-10_6_P64.dat           (int32 memmap)
kill_kind_K18_d-10_6_P64.dat      (uint8 memmap)
badpre_exitlow_K18_d-10_6_P64.bit (bitset)
rank_K18_d-10_6_P64.dat           (uint32 memmap)
```

Their SHA256 hashes and model parameters are canonical in:

```text
paper/artifacts.json
```

---

## 3) Run the verifier (single command)

From repo root:

```bash
python3 scripts/verify_full_theorem_K18_J10.py
```

Expected final line:

```text
[THEOREM VERIFY] OK
```

The verifier performs, in this order:

1. SHA256 verification of all 4 artifact files against `paper/artifacts.json`.
2. Rank monotonicity sample-check on live edges (2,000,000 samples).
3. Semantic-start unreachability check: `hit_r0 == 0`
   (start set `d = 0`, `r = 0` has no path to `exit_low`).
4. **FULL semantic check**: `exit_high` implies strict 1-step descent.
5. **FULL semantic check**: `shrink` implies strict 2-step descent.

If any check fails, the verifier terminates with an error.

---

## 4) Running on Windows

Use the same command. If your Python launcher is `py`:

```powershell
py scripts\verify_full_theorem_K18_J10.py
```

---

## 5) Custom bundle path

By default the verifier looks for the bundle directory:

```text
collatz_LT_K18_J10_bundle
```

You can override this with an environment variable.

### Linux / macOS

```bash
COLLATZ_BUNDLE_DIR=/path/to/bundle \
python3 scripts/verify_full_theorem_K18_J10.py
```

### Windows PowerShell

```powershell
$env:COLLATZ_BUNDLE_DIR="C:\path\to\bundle"
py scripts\verify_full_theorem_K18_J10.py
```

---

## 6) Canonical model parameters

* `K = 18` (modulus `2^18`, odd residues)
* `P = 64` (phase)
* `d` band = `[-10, 6]`

Packing `A`:

```text
sid = ((i * D + (d - dmin)) * P + r)
where i = a >> 1,  a = 2*i + 1
```

All details are specified in `verifier_spec.md`.

---

## 7) Canonical expected results

The verifier expects **exactly** the values recorded in
`paper/artifacts.json`, including:

* `hit_r0 == 0`
* `exit_high_count == 4,471,781` with `k`-range `[2, 17]`
* `shrink_count == 35,652,672`
* Zero counterexamples for:

  * `exit_high` descent
  * `shrink` 2-step descent

---

## 8) Optional: Colab / Google Drive

In Colab, the bundle can be stored in Drive, for example:

```text
/content/drive/MyDrive/collatz_LT_K18_J10_bundle
```

Set `COLLATZ_BUNDLE_DIR` accordingly and run the verifier.

---

## 9) One-line reproducibility claim

A reproduction is considered successful **iff**:

```bash
python3 scripts/verify_full_theorem_K18_J10.py
```

prints:

```text
[THEOREM VERIFY] OK
```

with no errors.

