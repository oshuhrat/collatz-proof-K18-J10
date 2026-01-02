## Zenodo (C1 J=20 FINAL)

Version DOI: https://doi.org/10.5281/zenodo.18133895  
Concept DOI (all versions): https://doi.org/10.5281/zenodo.18133894
# Reproducibility (C1, K=18, J=20)

This repository contains the source, the verifier, and a hash-fixed manifest for the **C1 final bundle** at:

- `K=18`, `P=64`
- deficit band `d ∈ [-20, 6]` (i.e. `J=20`)
- packing `A` (odd residues modulo `2^18`)

The proof is a **finite proof object** (bundle files) + an **independent verifier**.

## What is verified

The verifier checks:

- SHA256 integrity of all bundle files (as listed in `paper/artifacts_C1_J20.json`)
- schedule file `delta_P64.dat` (64 bytes, values in `{1,2}`)
- start coverage: every semantic start state `(a, d=0, r=0)` lies in `Pre*(Good)` (`goodpre`)
- ranking (termination) on live edges **restricted to the certified region** `goodpre==1`
- witness conditions at progress kills (`carry/exit_high/shrink2`)
- sampled semantic recomputation consistency (V1′) against the closed-form transition definition

A successful run prints exactly:
[THEOREM VERIFY] OK

text


## Option A: Verify from a ZIP bundle (recommended)

Place `bundle_C1_K18_J20_FINAL.zip` in the repo root (or provide its path).

Run:

```bash
python scripts/verify_C1_K18_J20.py \
  --bundle bundle_C1_K18_J20_FINAL.zip \
  --artifacts-json paper/artifacts_C1_J20.json
Expected final line:

text

[THEOREM VERIFY] OK
Optional: full goodpre recomputation (RAM-heavy)
This recomputes goodpre exactly from kill_kind and next and compares bit-for-bit:

Bash

python scripts/verify_C1_K18_J20.py \
  --bundle bundle_C1_K18_J20_FINAL.zip \
  --artifacts-json paper/artifacts_C1_J20.json \
  --heavy-goodpre
Option B: Verify from extracted files
If you downloaded the five bundle files directly (or extracted the ZIP), ensure the directory contains:

delta_P64.dat
kill_kind_K18_d-20_6_P64.dat
next_K18_d-20_6_P64.dat
goodpre_K18_d-20_6_P64.bit
rank_K18_d-20_6_P64.dat
Then run:

Bash

python scripts/verify_C1_K18_J20.py \
  --bundle /path/to/bundle_dir \
  --artifacts-json paper/artifacts_C1_J20.json
Compatibility note: Variant A (J10) vs C1 (J20)
This project previously contained an earlier certified bundle for a finite semantics theorem (Variant A):

K=18, P=64, band d ∈ [-10,6]
files: next.dat, kill_kind.dat, badpre_exitlow.bit, rank.dat
verifier: scripts/verify_full_theorem_K18_J10.py
The current release C1 (J=20) is a different semantics and a different proof bundle:

band d ∈ [-20,6]
includes an explicit schedule file delta_P64.dat
uses goodpre = Pre*(Good) and a rank certificate restricted to goodpre
verifier: scripts/verify_C1_K18_J20.py
These bundles are not interchangeable. Always use the verifier and paper/artifacts*.json matching the bundle you downloaded.

Troubleshooting
If you see FileNotFoundError, check the --bundle path.
If you see a SHA mismatch, ensure you are using the exact bundle referenced by paper/artifacts_C1_J20.json.





