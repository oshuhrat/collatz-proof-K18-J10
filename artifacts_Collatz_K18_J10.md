# Artifacts: Collatz LT bundle (K=18, dв€€[-10,6], P=64)

Zenodo (v1.0.0): https://doi.org/10.5281/zenodo.18114235
Zenodo (all versions): https://doi.org/10.5281/zenodo.18114234


All files are in:
`/content/drive/MyDrive/collatz_LT_K18_J10_bundle/`

## Parameters
- K=18
- P=64
- dmin=-10
- dmax=6
- N = 142,606,336 states

## Files + SHA256
- next_K18_d-10_6_P64.dat
  sha256: 51a1f8291b509769b65ab2e41e8a96f8d05c70ea8d57cb04aea3820c7b919334

- kill_kind_K18_d-10_6_P64.dat
  sha256: 21c8b89d08fa8149d53ec6f374a6fd315095bc205dcb9d4f8fe7a409999c4977

- badpre_exitlow_K18_d-10_6_P64.bit
  sha256: 562fae1d79678646c184f8e5deb5d93a7e454eac7995a09aceae922511c23ddd

- rank_K18_d-10_6_P64.dat
  sha256: 98c6cfe9d9fdc37eb3f78314e45c931e53f5194d50279ee66876bb1fbff32bb3

## Verified checks (as printed by verify_full_theorem)
- [OK] SHA256 matches expected
- [OK] rank sample verify (2,000,000 samples)
- [OK] hit_r0 == 0  (exit_low unreachable from starts d=0,r=0)
- exit_high FULL:
  exit_high count: 4,471,781
  k range: 2..17
- shrink FULL (2-step descent):
  shrink count: 35,652,672
- [THEOREM VERIFY] OK
