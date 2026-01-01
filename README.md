Zenodo (all versions): https://doi.org/10.5281/zenodo.18114234  
Review / feedback thread (GitHub Issue): https://github.com/oshuhrat/collatz-proof-K18-J10/issues/1

# Collatz (Project Alet) - Certified Proof Bundle (K=18, J=10)

Authors: **Shuhrat Okilov** and **Ulugbek Khamidov**  
Project: **Alet (Ethical AGI Development)**, Samarkand, Uzbekistan (independent researchers)

This repository contains a computationally certified proof bundle for the Collatz conjecture using an honest-cylinder finite-state model of the odd-only Collatz map at modulus `2^18`, with a 64-phase table and a deficit band `d in [-10, 6]`.

The proof is verified by a single script which must print the final line:
```text
[THEOREM VERIFY] OK
```

---

## What is included

* `paper/` вЂ” preprint sources (LaTeX) and appendix files.
* `paper/artifacts.json` вЂ” canonical artifact manifest (filenames, SHA256, parameters, expected counts).
* `scripts/verify_full_theorem_K18_J10.py` вЂ” the single verifier (cross-platform).
* `collatz_LT_K18_J10_bundle/` вЂ” required large binary artifacts (NOT suitable for normal git unless using LFS or external storage).

---

## Quick verification

### 1) Prepare artifacts

Put the four artifact files into:

```text
collatz_LT_K18_J10_bundle/
```

Files required:

* `next_K18_d-10_6_P64.dat`
* `kill_kind_K18_d-10_6_P64.dat`
* `badpre_exitlow_K18_d-10_6_P64.bit`
* `rank_K18_d-10_6_P64.dat`

---

### 2) Run the verifier

```bash
python3 scripts/verify_full_theorem_K18_J10.py
```

Expected output:

```text
[THEOREM VERIFY] OK
```

---

## Artifact integrity

All artifact SHA256 hashes and expected verification counts are recorded in:

```text
paper/artifacts.json
```

The verifier checks these values exactly and aborts on any mismatch.

---

## License

Choose and add a `LICENSE` file (e.g., MIT) as needed.



