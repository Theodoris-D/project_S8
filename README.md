# PUDA -- Privacy and Unforgeability for Data Aggregation (Rust implementation)

Rust implementation of the **PUDA** protocol on the BLS12-381 pairing-friendly curve, plus an extension using a **KBS** (Key-Binding Scheme), developed as a student cryptography project at EURECOM (Fall 2025).

**Reference paper:** I. Leontiadis, K. Elkhiyaoui, M. Önen, R. Molva, *PUDA – Privacy and Unforgeability for Data Aggregation*, CANS 2015, LNCS 9476, pp. 3–18. [PDF (EURECOM)](https://www.eurecom.fr/publication/4672/download/rs-publi-4672_1.pdf) · [EURECOM page](https://www.eurecom.fr/en/publication/4672) · DOI: [10.1007/978-3-319-26823-1_1](https://doi.org/10.1007/978-3-319-26823-1_1)

The original PUDA aggregates single values; this implementation follows the vector variant ("PUDA over Vectors") with OPRF key binding from *Verifiable Secure Aggregation with Malicious Clients and Aggregator* (Ben Jaballah, Faonio, Manam, Mansouri, Önen; under submission). The protocol designs come from these papers; this repository contains my implementation, benchmarks and presentation.

---

## What is in this repository

| Folder | Content | Status |
|--------|---------|--------|
| [`puda-rust/`](puda-rust/) | Rust crate: PUDA protocol (Setup, EncTag, Aggregate, Verify), KBS module, CLI, benchmark runner, tests | Builds; tests pass |
| [`puda-rust/wip/`](puda-rust/wip/) | Draft of a standalone KBS binary | Work in progress, **not compiled** (excluded from `Cargo.toml`) |
| [`benchmarks/`](benchmarks/) | Python scripts to run benchmarks and plot results, raw results (`benchmark_results.csv`), generated figures | Supporting material |
| [`presentation/`](presentation/) | Project slides: [`presentation_puda.pdf`](presentation/presentation_puda.pdf) and LaTeX source | Final |

**Part of the project (implemented and tested):** the four PUDA phases and the KBS protocol module (`src/puda/kbs.rs`), validated by the 6 tests in `tests/protocol_tests.rs`.
**Not part of the delivered implementation:** the zero-knowledge proof `pi_U` in KBS is a dummy placeholder, and `wip/kbs_main.rs` is an unfinished draft.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Architecture](#project-architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Usage](#usage)
   - [PUDA Protocol](#puda-protocol)
   - [KBS Protocol](#kbs-protocol)
   - [Benchmarks](#benchmarks)
   - [Tests](#tests)
6. [Protocol Description](#protocol-description)
   - [PUDA](#puda---private-user-data-aggregation)
   - [KBS](#kbs---key-binding-scheme)
7. [Module Documentation](#module-documentation)
8. [Test Documentation](#test-documentation)
9. [DLP Memory Analysis](#dlp-memory-analysis)
10. [Dependencies](#dependencies)
11. [Presentation](#presentation)
12. [Authors](#authors)

---

## Overview

This project implements two complementary cryptographic protocols:

- **PUDA**: Enables an aggregator to compute the sum of private user data without seeing individual values, with verification through bilinear pairings on BLS12-381.
- **KBS**: A Key-Binding Scheme based on a 2HashDH OPRF (Oblivious Pseudo-Random Function), allowing a user to obtain a signed tag from a tagger only if both share the same key.

Both protocols are built on the **Arkworks** ecosystem for elliptic curve arithmetic and pairings.

---

## Project Architecture

```
.
├── README.md
├── puda-rust/                         # Rust crate (the implementation)
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs                     # Library root (pub mod puda)
│   │   ├── bin/
│   │   │   └── benchmark_runner.rs    # Automated benchmark runner
│   │   └── puda/
│   │       ├── mod.rs                 # Sub-module declarations
│   │       ├── models.rs              # Data structures (PublicParams, keys, etc.)
│   │       ├── utils.rs               # Hash-to-curve, DLP table, map_to_group
│   │       ├── data_aggregator.rs     # Setup + Aggregation
│   │       ├── data_analyzer.rs       # Pairing-based verification
│   │       ├── user.rs                # EncTag (user-side encryption + tagging)
│   │       ├── kbs.rs                 # KBS protocol (OPRF, rounds 1-2)
│   │       └── main.rs                # PUDA binary entry point (demo/benchmark)
│   ├── tests/
│   │   └── protocol_tests.rs          # 6 statistical tests (PUDA + KBS)
│   └── wip/
│       └── kbs_main.rs                # Unfinished standalone KBS binary (not built)
│
├── benchmarks/                        # Benchmark & plotting scripts (Python)
│   ├── analyze_result.py              # Plots from benchmark_results.csv
│   ├── benchmark_comprehensive.py     # Full benchmark campaign
│   ├── benchmark_federated.py         # Federated-learning-sized benchmarks
│   ├── generate_graphs.py             # Presentation figures
│   ├── benchmark_results.csv          # Raw results
│   └── figures/                       # Generated graphs
│
└── presentation/
    ├── presentation_puda.pdf          # Slides
    ├── presentation_puda.tex          # Beamer source
    └── figures/                       # Figures used in the slides
```

### Binaries

| Name | Path | Description |
|------|------|-------------|
| `puda` | `src/puda/main.rs` | Runs the PUDA protocol (demo or benchmark mode) |
| `benchmark_runner` | `src/bin/benchmark_runner.rs` | Parametric benchmark orchestrator |

### Library

The crate exposes the `puda` library (defined in `src/lib.rs`), accessible via:
```rust
use puda::puda::{models, utils, data_aggregator, data_analyzer, user, kbs};
```

---

## Prerequisites

- **Rust** >= 1.70 (edition 2021)
- **Cargo** (bundled with Rust)
- **Python 3** (optional, for graph generation)
  - `pandas`, `matplotlib`, `seaborn`, `scipy`

---

## Installation

```bash
git clone https://github.com/Theodoris-D/puda-verifiable-aggregation.git
cd puda-verifiable-aggregation/puda-rust
cargo build --release
```

The first build will compile the Arkworks dependencies (~2-5 min in release mode).

---

## Usage

### PUDA Protocol

**Demo mode** (verbose output, single run):

```bash
cargo run --release --bin puda -- --demo
```

**Benchmark mode** (configurable):

```bash
cargo run --release --bin puda -- \
    --num-users 10 \
    --kappa 3 \
    --min-value 0 \
    --max-value 100 \
    --number-of-trials 50 \
    --random-seed
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `-d, --demo` | `false` | Demo mode with verbose output |
| `-n, --num-users` | `7` | Number of participating users |
| `-k, --kappa` | `2` | Data vector dimension |
| `--min-value` | `0` | Minimum data value |
| `-m, --max-value` | `20` | Maximum data value |
| `-t, --number-of-trials` | `1` | Number of iterations (results are averaged) |
| `-r, --random-seed` | `false` | Random seed (otherwise deterministic) |

**Constraint**: `num_users * max_value < 65536` (DLP lookup table limit).

Results are saved to `benchmark_results.csv`.

### KBS Protocol

The KBS protocol is implemented as a library module (`puda::puda::kbs`) and is exercised through the test suite (tests 4-6, see [Test Documentation](#test-documentation)):

```bash
cargo test --release --test protocol_tests kbs -- --nocapture
```

A standalone `kbs` binary was started in `wip/kbs_main.rs` but is unfinished and not part of the build.

### Benchmarks

The **benchmark runner** automatically executes the PUDA binary across a parameter grid:

```bash
cargo run --release --bin benchmark_runner -- \
    --number-of-trials 10 \
    --max-users 100 \
    --max-kappa 10 \
    --number-of-x 5 \
    --number-of-y 3 \
    --max-value 500
```

Benchmark runner options:

| Flag | Default | Description |
|------|---------|-------------|
| `--number-of-trials` | `10` | Iterations per configuration |
| `--max-users` | `100` | Maximum number of users |
| `--max-kappa` | `10` | Maximum vector dimension |
| `--number-of-x` | `5` | Measurement points for num_users |
| `--number-of-y` | `3` | Measurement points for kappa |
| `--max-value` | `500` | Maximum data value |
| `--generate-graphs` | `true` | Generate graphs with `../benchmarks/analyze_result.py` (requires Python) |

### Tests

Run all 6 statistical tests:

```bash
cargo test --test protocol_tests -- --nocapture
```

Or run all project tests:

```bash
cargo test -- --nocapture
```

The first run initializes the DLP lookup table (~1-2s), then the 6 tests execute (100 iterations each).

---

## Protocol Description

### PUDA - Private User Data Aggregation

The PUDA protocol enables verifiable aggregation of private data. It proceeds in 4 phases:

#### Phase 1: Setup (`data_aggregator::setup`)

A trusted **Data Dealer** generates the parameters:
- **Public parameters**: `pp = (P1, P2)` (generators of G1 and G2 on BLS12-381)
- **User keys**: for each user `i`:
  - `ek_i`: encryption key (random scalar)
  - `tk_i = (a, b_i)`: tag key, where `a = (a_1, ..., a_kappa)` is shared across all users and `b_i` is unique to each user
- **Aggregator key**: `ska = -sum(ek_i)` (cancels the encryption masks during aggregation)
- **Verification key**: `vk = (vk_a, vk_b)` where `vk_a[k] = P2 * a_k` and `vk_b[i] = P2 * b_i`

#### Phase 2: EncTag (`user::enc_tag`)

Each user `i` encrypts their vector `x_i = (x_i1, ..., x_ik)`:
- **Ciphertext**: `c_ik = P1 * x_ik + H(tau||k) * ek_i`
- **Tag**: `sigma_i = H(tau) * b_i + sum(a_k * x_ik) * P1`

The parameter `tau` is a session/timestamp identifier.

#### Phase 3: Aggregate (`data_aggregator::aggregate`)

The aggregator computes for each dimension `k`:
- `V_k = sum(c_ik) + H(tau||k) * ska`
- The terms `H(tau||k) * ek_i` cancel with `ska = -sum(ek_i)`, leaving `V_k = P1 * sum(x_ik)`
- `x_k = DLP(V_k)` via the precomputed lookup table

It also computes `gamma = sum(sigma_i)`.

#### Phase 4: Verify (`data_analyzer::verify`)

Verification through bilinear pairings:
```
e(gamma, P2) == prod_k(e(P1 * x_k, vk_a[k])) * prod_i(e(H(tau), vk_b[i]))
```

If the equality holds, the aggregated sums are correct and have not been tampered with.

### KBS - Key-Binding Scheme

The KBS protocol allows a user to obtain a signed tag `sigma` from the tagger, conditioned on both parties sharing the same OPRF key. The protocol uses a 2HashDH-based OPRF.

#### Actors

- **User**: holds a vector `x`, a key `k_u_j` (obtained from a CMP)
- **Tagger**: holds a tag key `(a_j, b_j)`, an OPRF key `k1_j`, and a scalar `gamma_j`

#### Round 1

1. **User** (`kbs::user_prepare_message`):
   - Samples random `r_j`
   - Computes `c_j[k] = P1 * x_k * r_j` and `d_j = H(sid||ssid) * r_j`
   - Generates a proof `pi_U` (dummy in the current implementation)
   - Sends `(c_j, d_j, pi_U)` to the tagger

2. **Tagger** (`kbs::tagger_process`):
   - Verifies `pi_U`
   - Computes `e_j = sum(c_jk * a_jk) + d_j * b_j`
   - Derives the OPRF key: `rho_T = H_2(k1_j || H_1(k1_j) * gamma_j)`
   - Encrypts `(e_j || pi_T)` under `rho_T` with AES-256-GCM
   - Returns the ciphertext and `H_1(k1_j) * gamma_j`

#### Round 2 (OPRF)

3. **User** (`kbs::user_oprf_eval`):
   - Samples random `s_j`
   - Computes `f_j = H_1(k_u_j) * s_j` and sends it to the tagger

4. **Tagger** (`kbs::tagger_oprf_complete`):
   - Computes `f'_j = f_j * gamma_j` and returns it

5. **User** (`kbs::user_complete`):
   - Computes `rho_U = H_2(k_u_j || f'_j / s_j)`
   - If `k_u_j == k1_j`, then `rho_U == rho_T` and decryption succeeds
   - Otherwise, AES-GCM decryption fails and returns `None`
   - On success, computes `sigma = e_j / r_j`

#### Hash Functions

- `H_1`: hash-to-curve (reuses `map_to_group` from GLS Section 3.2)
- `H_2`: hash to 256-bit symmetric key (SHA-256)

---

## Module Documentation

### `models.rs` -- Data Structures

| Structure | Fields | Description |
|-----------|--------|-------------|
| `PublicParams` | `p_1: G1`, `p_2: G2` | Group generators |
| `UserSecretKey` | `id`, `ek`, `tk: (Vec<ScalarField>, ScalarField)` | User secret key (encryption + tag) |
| `AggregatorSecretKey` | `ska: ScalarField` | Aggregator secret key |
| `DataDealerVK` | `vk_a: Vec<G2>`, `vk_b: Vec<G2>` | Data Dealer verification key |
| `CiphertextAndTag` | `c: Vec<G1>`, `sigma: G1` | User ciphertext and tag |

Types re-exported from Arkworks:
- `G1 = G1Projective` (BLS12-381 curve points, group G1)
- `G2 = G2Projective` (curve points, group G2)
- `ScalarField = Fr` (scalars modulo the subgroup order)

### `utils.rs` -- Cryptographic Utilities

| Function | Signature | Description |
|----------|-----------|-------------|
| `map_to_group` | `(message: &str) -> G1` | Hash-to-curve (GLS Section 3.2, try-and-increment) |
| `find_discrete_log` | `(target: G1) -> u64` | Recovers `x` such that `target = x * G1` via precomputed table |

The DLP table is lazily initialized (`OnceLock`) with 65,536 entries (~9 MB).

### `data_aggregator.rs` -- Setup and Aggregation

| Function | Signature | Description |
|----------|-----------|-------------|
| `setup` | `(num_users, rng, kappa) -> (PublicParams, Vec<UserSecretKey>, AggregatorSecretKey, DataDealerVK)` | Generates all parameters and keys |
| `aggregate` | `(agg_sk, inputs, tau, kappa, pp) -> (Vec<u64>, G1)` | Aggregates ciphertexts and returns `(sums, gamma)` |

### `user.rs` -- User-Side Encryption

| Function | Signature | Description |
|----------|-----------|-------------|
| `enc_tag` | `(uk, x_i, tau, kappa, pp) -> CiphertextAndTag` | Encrypts vector `x_i` and computes tag `sigma_i` |

### `data_analyzer.rs` -- Verification

| Function | Signature | Description |
|----------|-----------|-------------|
| `verify` | `(data_vk, gamma, x_tau, tau, kappa, pp) -> bool` | Verifies integrity via bilinear pairings |

### `kbs.rs` -- KBS Protocol

| Function | Signature | Description |
|----------|-----------|-------------|
| `user_prepare_message` | `(x, sid, ssid, pp, k_u_j, rng) -> (UserMessage, UserLocalState)` | Round 1: user message preparation |
| `tagger_process` | `(user_msg, k_tag, oprf_state, sid, ssid, pp, rng) -> Option<TaggerMessage>` | Round 1: tagger-side processing |
| `user_oprf_eval` | `(state, rng) -> G1` | Round 2: user-side OPRF evaluation |
| `tagger_oprf_complete` | `(f_j, gamma_j) -> G1` | Round 2: tagger-side OPRF completion |
| `user_complete` | `(state, tagger_msg, f_prime_j, user_msg) -> Option<G1>` | Finalization: decryption and sigma extraction |

KBS structures:

| Structure | Fields | Description |
|-----------|--------|-------------|
| `TaggerKey` | `a_j: Vec<ScalarField>`, `b_j: ScalarField` | Tagger's tag key |
| `OPRFState` | `gamma_j: ScalarField`, `k1_j: G1` | Tagger's OPRF state |
| `UserMessage` | `c_j: Vec<G1>`, `d_j: G1`, `proof_u: ProofRU` | User -> Tagger message |
| `UserLocalState` | `r_j`, `s_j`, `k_u_j` | User's local state (never sent) |
| `TaggerMessage` | `ciphertext`, `nonce`, `h1_gamma: G1` | Tagger -> User message |

---

## Test Documentation

The file `tests/protocol_tests.rs` contains 6 statistical tests, each executed **100 times** (`NUM_TRIALS = 100`) with randomized parameters.

### Parameters Varied Per Iteration

| Parameter | Range |
|-----------|-------|
| `num_users` | [2, 20] |
| `kappa` | [1, 5] |
| User data | [0, 65535 / num_users] |
| KBS keys | Random scalars/points |
| `sid`, `ssid` | Random alphanumeric strings (8 characters) |

### PUDA Tests

| # | Name | Invariant | Description |
|---|------|-----------|-------------|
| 1 | `test_puda_aggregate_correctness` | `aggregated_sum[k] == sum(user_data[i][k])` | Verifies the aggregated sum matches the plaintext sum exactly |
| 2 | `test_puda_verify_valid` | `verify() == true` | Verifies pairing-based verification always accepts an honest aggregation |
| 3 | `test_puda_verify_rejects_tampered` | `verify() == false` | Verifies verification always rejects a tampered sum (1 randomly modified element) |

### KBS Tests

| # | Name | Invariant | Description |
|---|------|-----------|-------------|
| 4 | `test_kbs_matching_keys_success` | `user_complete() == Some(sigma)` and `sigma == sum(x_k * a_k) * P1 + H(sid\|\|ssid) * b` | Verifies the protocol succeeds when `k1_j == k_u_j`, and sigma has the expected value |
| 5 | `test_kbs_mismatched_keys_failure` | `user_complete() == None` | Verifies decryption fails when `k1_j != k_u_j` |
| 6 | `test_kbs_oprf_key_agreement` | `rho_T == rho_U` | Directly verifies OPRF key agreement without going through encryption |

### Running Tests

```bash
# All tests
cargo test -- --nocapture

# A specific test
cargo test test_kbs_matching_keys_success -- --nocapture
```

---

## DLP Memory Analysis

The discrete log lookup table (`find_discrete_log`) is precomputed with `DLP_TABLE_SIZE = 65536` entries.

| Size | Entries | RAM | Time | Status |
|------|---------|-----|------|--------|
| 2^16 | 65K | ~9 MB | ~1s | OK |
| 2^24 | 16M | 1.73 GB | ~2.5 min | OK |
| 2^26 | 64M | 3.87 GB | ~16 min | OK (swap pressure) |
| 2^27 | 128M | >8 GB | >20 min | Thrashing |

Cost per entry: ~60 bytes (48 bytes compressed G1 + 8 bytes u64 + HashMap overhead).

In practice, 2^16 is sufficient for the aggregated sums in the PUDA protocol.

---

## Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| `ark-bls12-381` | 0.4.0 | BLS12-381 curve |
| `ark-ec` | 0.4.0 | Elliptic curve arithmetic |
| `ark-ff` | 0.4.0 | Finite fields |
| `ark-poly` | 0.4.0 | Polynomials |
| `ark-std` | 0.4.0 | Utilities (RNG, traits) |
| `ark-serialize` | 0.4.0 | Point serialization |
| `aes-gcm` | 0.10 | Symmetric encryption (KBS) |
| `sha2` | 0.10.6 | Hash functions |
| `serde` | 1.0 | Serialization |
| `bincode` | 1.3 | Binary serialization |
| `hex` | 0.4 | Hexadecimal encoding |
| `rand` | 0.8.5 | Random number generation |
| `clap` | 4.5 | CLI argument parsing |

---

## Presentation

The slides are in [`presentation/presentation_puda.pdf`](presentation/presentation_puda.pdf). To rebuild them from source:

```bash
cd presentation
latexmk -pdf presentation_puda.tex
```

---

## Authors

Implementation by Theodoris Donval, Cryptography project, EURECOM, Fall 2025.
Protocol: Leontiadis, Elkhiyaoui, Önen and Molva (CANS 2015), see the [reference paper](https://www.eurecom.fr/publication/4672/download/rs-publi-4672_1.pdf).
