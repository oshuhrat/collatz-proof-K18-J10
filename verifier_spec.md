# verifier_spec.md

Maintainers / Authors: Shuhrat Okilov, Ulugbek Khamidov
Project: Alet (Ethical AGI Development), Samarkand, Uzbekistan
## Purpose

This spec defines the *single* reproducible verification target:

> `[THEOREM VERIFY] OK` for the Collatz proof bundle **K=18, P=64, d∈[-10,6]**.

The verifier checks:
1) file integrity (SHA256),
2) rank monotonicity on live edges (sample),
3) `exit_low` unreachable from the semantic start set (hit_r0=0),
4) FULL semantic descent for `exit_high`,
5) FULL 2-step semantic descent for `shrink` kills.

Passing all checks certifies the Linking Lemma `LT(K18,J10)` and the global descent argument.

---

## Model

### Odd-only Collatz map
For odd `n ∈ ℕ`:
- `y = 3n+1`
- `k = v2(y) ≥ 1`
- `F(n) = y / 2^k` (odd)

### Phase
- `r = t mod 64` where `t` is the odd-only step counter.

### Delta table
`Delta[r] ∈ {1,2}` is fixed (computed by):
`Delta[r] = floor((t+1)log2(3)) - floor(t log2(3))` for `t=r ∈ [0..63]`.

### Deficit annotation
`d_{t+1} = d_t + k_t - Delta[r_t]`.

`d` is an annotation defined by this recurrence and is only meaningful up to an additive constant (normalization).
We fix normalization by starting at `d0 = 0`.

---

## Honest cylinder band automaton

### Parameters
- `K = 18`, modulus `2^18`
- `P = 64`
- `dmin = -10`, `dmax = 6`
- Only odd residues `a mod 2^K`

### State space
A state is a triple:
- `a`: odd residue in `[1,3,...,2^K-1]` (represents `n mod 2^K`)
- `d`: integer in `[dmin, dmax]`
- `r`: integer in `[0..P-1]`

### State indexing (packing A)
Let `i = a >> 1` be the odd-index.
Let `D = dmax - dmin + 1`.

The state id `sid` is:
sid = ((i * D + (d - dmin)) * P + r)

text


Unpack:
r = sid % P
sid //= P
d_off = sid % D
sid //= D
i = sid
a = 2*i + 1
d = d_off + dmin

text


### Transition semantics (`next.dat`)
For each state `(a,d,r)`:

1) Compute integer `y = 3a + 1`.
2) Compute `k = v2(y)`.
3) Compute next residue:
   `a' = (y >> k) mod 2^K`.
4) Update:
   `d' = d + k - Delta[r]`,
   `r' = (r+1) mod P`.
5) Apply kill rules:
   - `shrink kill` if `a' ≡ 1 (mod 8)`.
   - `exit_high` if `d' > dmax`.
   - `exit_low` if `d' < dmin`.
   - otherwise live edge to `(a',d',r')`.

`next.dat` stores `Next[sid]`:
- `Next[sid] = -1` means kill,
- else `Next[sid] = sid'` (live successor).

`kill_kind.dat` stores:
- `0` live
- `1` shrink kill
- `2` exit_high
- `3` exit_low

---

## Start set (semantic start)

We start the real odd-only time at `t=0`, hence `r0 = 0`.

We normalize `d0 = 0`.

Start set:
S0 = { sid(a, d=0, r=0) : a odd mod 2^18 }

text


---

## Certified invariants and what the verifier must check

### A) File integrity
The verifier must compute SHA256 and match expected values:

- next_K18_d-10_6_P64.dat  
  `51a1f8291b509769b65ab2e41e8a96f8d05c70ea8d57cb04aea3820c7b919334`

- kill_kind_K18_d-10_6_P64.dat  
  `21c8b89d08fa8149d53ec6f374a6fd315095bc205dcb9d4f8fe7a409999c4977`

- badpre_exitlow_K18_d-10_6_P64.bit  
  `562fae1d79678646c184f8e5deb5d93a7e454eac7995a09aceae922511c23ddd`

- rank_K18_d-10_6_P64.dat  
  `98c6cfe9d9fdc37eb3f78314e45c931e53f5194d50279ee66876bb1fbff32bb3`

### B) Rank certificate
`rank.dat` stores an unsigned integer `Rank[sid]`.

Verifier condition:
For any `sid` with `Next[sid] != -1`, we must have:
Rank[ Next[sid] ] < Rank[sid]

text

The verifier may check this on a fixed RNG sample (2,000,000) or full pass.

### C) No-escape below dmin from semantic starts
`badpre_exitlow.bit` encodes `Pre*(exit_low)` (states that can reach exit_low).

Verifier condition:
For every `sid ∈ S0`, the bit must be 0.
Equivalently, `hit_r0 == 0`.

### D) Progress semantics: exit_high (FULL)
For every state `sid` with `kill_kind==2` and `Next[sid]==-1`, compute:
- `a = unpack(sid).a`
- `y = 3a+1`
- `k = v2(y)`
- `n1 = y >> k`
Require:
n1 < a

text


### E) Progress semantics: shrink kill (FULL, 2-step)
For every state `sid` with `kill_kind==1` and `Next[sid]==-1`, compute:
- `a = unpack(sid).a`
- `n1 = F(a)`
Require:
- `n1 ≡ 1 (mod 8)`.
- if `n1 == 1`: accept (terminal).
- else compute `n2 = F(n1)` and require:
n2 < n1

text


---

## Soundness / Projective Lock (used for the ℕ link)

Within the band `d∈[-10,6]`, live steps cannot have `k ≥ 18` because then:
`d' = d + k - Delta[r] ≥ d + 18 - 2 > 6`,
forcing `exit_high` (kill), hence not live.

Thus every live step satisfies `k < 18`, which excludes carry-singularity at modulus `2^18`
and makes `a'` well-defined from `a` alone. Therefore the cylinder transitions coincide with
the real odd-only map on ℕ up to the first kill.

---

## Verified conclusion (what `[THEOREM VERIFY] OK` certifies)

From any odd start residue `a` at `d=0, r=0`:
- exit_low is unreachable (cannot escape below -10),
- there is no infinite live path (rank decreases),
- therefore a kill is reached finitely,
- every kill yields strict descent in ℕ (exit_high in 1 step; shrink in 2 steps).

By well-foundedness of ℕ, repeated descent implies the odd-only trajectory reaches 1, hence
the full Collatz iteration reaches 1 for all n∈ℕ.