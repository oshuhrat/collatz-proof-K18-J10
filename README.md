Zenodo (all versions): https://doi.org/10.5281/zenodo.18114234
Review / feedback thread (GitHub Issue): https://github.com/oshuhrat/collatz-proof-K18-J10/issues/1

# Collatz (Project Alet) - Certified Proof Bundle (K=18, J=10)

Authors: Shuhrat Okilov and Ulugbek Khamidov
Project: Alet (Ethical AGI Development), Samarkand, Uzbekistan (independent researchers)

This repository contains a computationally certified proof bundle for the Collatz conjecture using an honest-cylinder finite-state model of the odd-only Collatz map at modulus 2^18, with a 64-phase table and a deficit band d in [-10, 6].

Verification is successful iff the verifier prints the final line:
[THEOREM VERIFY] OK

## Files in this repository
- paper/ (LaTeX preprint sources and appendix)
- verifier_spec.md (formal model specification)
- scripts/verify_full_theorem_K18_J10.py (single end-to-end verifier)
- paper/artifacts.json (canonical manifest: SHA256 + parameters + expected counts)

## Bundle artifacts (binary data)
The large binary artifacts are archived on Zenodo:
https://doi.org/10.5281/zenodo.18114234

After downloading, place these four files into:
collatz_LT_K18_J10_bundle/

Required filenames:
- next_K18_d-10_6_P64.dat
- kill_kind_K18_d-10_6_P64.dat
- badpre_exitlow_K18_d-10_6_P64.bit
- rank_K18_d-10_6_P64.dat

## Quick verification
1) Install numpy:
python -m pip install numpy

2) Run verifier:
python3 scripts/verify_full_theorem_K18_J10.py

Expected final line:
[THEOREM VERIFY] OK

## License
MIT license is provided in LICENSE.
