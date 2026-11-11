use puda::puda::data_aggregator::{setup, aggregate};
use puda::puda::data_analyzer::verify;
use puda::puda::user::enc_tag;
use puda::puda::models::*;
use puda::puda::utils::map_to_group;
use puda::puda::kbs::*;

use ark_std::rand::{rngs::StdRng, SeedableRng, Rng};
use ark_std::UniformRand;

const NUM_TRIALS: usize = 100;

// ============================================================================
// Helper: generate random alphanumeric string
// ============================================================================
fn random_string(rng: &mut StdRng, len: usize) -> String {
    const CHARSET: &[u8] = b"abcdefghijklmnopqrstuvwxyz0123456789";
    (0..len)
        .map(|_| {
            let idx = rng.gen::<usize>() % CHARSET.len();
            CHARSET[idx] as char
        })
        .collect()
}

// ============================================================================
// PUDA TESTS
// ============================================================================

#[test]
fn test_puda_aggregate_correctness() {
    let mut rng = StdRng::seed_from_u64(42);

    for trial in 0..NUM_TRIALS {
        let num_users = 2 + rng.gen::<usize>() % 19; // [2, 20]
        let kappa = 1 + rng.gen::<usize>() % 5;       // [1, 5]
        let max_val = 65535u64 / (num_users as u64);
        let tau: u64 = rng.gen::<u64>() % 1_000_000;

        let (pp, user_keys, aggregator_key, _vk) = setup(num_users, &mut rng, kappa);

        // Generate random user data and compute expected sums
        let mut user_data: Vec<Vec<u64>> = Vec::new();
        let mut expected_sums = vec![0u64; kappa];

        for _i in 0..num_users {
            let data: Vec<u64> = (0..kappa)
                .map(|_| rng.gen::<u64>() % (max_val + 1))
                .collect();
            for k in 0..kappa {
                expected_sums[k] += data[k];
            }
            user_data.push(data);
        }

        // Encrypt
        let user_inputs: Vec<CiphertextAndTag> = (0..num_users)
            .map(|i| enc_tag(&user_keys[i], user_data[i].clone(), tau, kappa, &pp))
            .collect();

        // Aggregate
        let (aggregated_sum, _gamma) = aggregate(&aggregator_key, &user_inputs, tau, kappa, &pp);

        // Check invariant
        assert_eq!(
            aggregated_sum, expected_sums,
            "Trial {}: aggregated sum mismatch (n={}, k={})",
            trial, num_users, kappa
        );
    }
}

#[test]
fn test_puda_verify_valid() {
    let mut rng = StdRng::seed_from_u64(123);

    for trial in 0..NUM_TRIALS {
        let num_users = 2 + rng.gen::<usize>() % 19;
        let kappa = 1 + rng.gen::<usize>() % 5;
        let max_val = 65535u64 / (num_users as u64);
        let tau: u64 = rng.gen::<u64>() % 1_000_000;

        let (pp, user_keys, aggregator_key, vk) = setup(num_users, &mut rng, kappa);

        let user_data: Vec<Vec<u64>> = (0..num_users)
            .map(|_| {
                (0..kappa)
                    .map(|_| rng.gen::<u64>() % (max_val + 1))
                    .collect()
            })
            .collect();

        let user_inputs: Vec<CiphertextAndTag> = (0..num_users)
            .map(|i| enc_tag(&user_keys[i], user_data[i].clone(), tau, kappa, &pp))
            .collect();

        let (sum, gamma) = aggregate(&aggregator_key, &user_inputs, tau, kappa, &pp);

        let valid = verify(&vk, gamma, sum, tau, kappa, &pp);
        assert!(
            valid,
            "Trial {}: verify should return true for valid aggregation (n={}, k={})",
            trial, num_users, kappa
        );
    }
}

#[test]
fn test_puda_verify_rejects_tampered() {
    let mut rng = StdRng::seed_from_u64(999);

    for trial in 0..NUM_TRIALS {
        let num_users = 2 + rng.gen::<usize>() % 19;
        let kappa = 1 + rng.gen::<usize>() % 5;
        let max_val = 65535u64 / (num_users as u64);
        let tau: u64 = rng.gen::<u64>() % 1_000_000;

        let (pp, user_keys, aggregator_key, vk) = setup(num_users, &mut rng, kappa);

        let user_data: Vec<Vec<u64>> = (0..num_users)
            .map(|_| {
                (0..kappa)
                    .map(|_| rng.gen::<u64>() % (max_val + 1))
                    .collect()
            })
            .collect();

        let user_inputs: Vec<CiphertextAndTag> = (0..num_users)
            .map(|i| enc_tag(&user_keys[i], user_data[i].clone(), tau, kappa, &pp))
            .collect();

        let (mut sum, gamma) = aggregate(&aggregator_key, &user_inputs, tau, kappa, &pp);

        // Tamper with a random element
        let tamper_idx = rng.gen::<usize>() % kappa;
        sum[tamper_idx] = sum[tamper_idx].wrapping_add(1 + rng.gen::<u64>() % 100);

        let valid = verify(&vk, gamma, sum, tau, kappa, &pp);
        assert!(
            !valid,
            "Trial {}: verify should return false for tampered sum (n={}, k={}, tampered index={})",
            trial, num_users, kappa, tamper_idx
        );
    }
}

// ============================================================================
// KBS TESTS
// ============================================================================

#[test]
fn test_kbs_matching_keys_success() {
    let mut rng = StdRng::seed_from_u64(7777);
    let pp = PublicParams {
        p_1: G1::generator(),
        p_2: G2::generator(),
    };

    for trial in 0..NUM_TRIALS {
        let kappa = 1 + rng.gen::<usize>() % 5;
        let sid = random_string(&mut rng, 8);
        let ssid = random_string(&mut rng, 8);

        // Random user data
        let x: Vec<ScalarField> = (0..kappa)
            .map(|_| ScalarField::rand(&mut rng))
            .collect();

        // Tagger key
        let a_j: Vec<ScalarField> = (0..kappa)
            .map(|_| ScalarField::rand(&mut rng))
            .collect();
        let b_j = ScalarField::rand(&mut rng);
        let k_tag = TaggerKey {
            a_j: a_j.clone(),
            b_j,
        };

        // OPRF state: gamma_j random, k1_j = k_u_j (matching keys)
        let gamma_j = ScalarField::rand(&mut rng);
        let k_shared = G1::rand(&mut rng); // same key for both
        let oprf_state = OPRFState {
            gamma_j,
            k1_j: k_shared,
        };

        // Round 1: User prepares message
        let (user_msg, mut local_state) =
            user_prepare_message(&x, &sid, &ssid, &pp, k_shared, &mut rng);

        // Round 1: Tagger processes
        let tagger_msg = tagger_process(&user_msg, &k_tag, &oprf_state, &sid, &ssid, &pp, &mut rng)
            .expect("tagger_process should succeed");

        // Round 2: User OPRF eval
        let f_j = user_oprf_eval(&mut local_state, &mut rng);

        // Round 2: Tagger OPRF complete
        let f_prime_j = tagger_oprf_complete(&f_j, &gamma_j);

        // User completes
        let result = user_complete(&local_state, &tagger_msg, &f_prime_j, &user_msg);
        assert!(
            result.is_some(),
            "Trial {}: user_complete should return Some(sigma) when keys match (k={})",
            trial, kappa
        );

        // Verify sigma = sum(x_k * a_k) * P1 + H(sid||ssid) * b_j
        let sigma = result.unwrap();
        let mut expected_sigma = G1::zero();
        for k in 0..kappa {
            expected_sigma += pp.p_1 * (x[k] * a_j[k]);
        }
        let h_sid_ssid = map_to_group(&format!("{}||{}", sid, ssid));
        expected_sigma += h_sid_ssid * b_j;

        assert_eq!(
            sigma, expected_sigma,
            "Trial {}: sigma mismatch with expected value (k={})",
            trial, kappa
        );
    }
}

#[test]
fn test_kbs_mismatched_keys_failure() {
    let mut rng = StdRng::seed_from_u64(8888);
    let pp = PublicParams {
        p_1: G1::generator(),
        p_2: G2::generator(),
    };

    for trial in 0..NUM_TRIALS {
        let kappa = 1 + rng.gen::<usize>() % 5;
        let sid = random_string(&mut rng, 8);
        let ssid = random_string(&mut rng, 8);

        let x: Vec<ScalarField> = (0..kappa)
            .map(|_| ScalarField::rand(&mut rng))
            .collect();

        let k_tag = TaggerKey {
            a_j: (0..kappa).map(|_| ScalarField::rand(&mut rng)).collect(),
            b_j: ScalarField::rand(&mut rng),
        };

        // Different keys: k1_j != k_u_j
        let k1_j = G1::rand(&mut rng);
        let k_u_j = G1::rand(&mut rng);
        // Extremely unlikely they are equal, but guard against it
        assert_ne!(
            g1_to_bytes(&k1_j),
            g1_to_bytes(&k_u_j),
            "Trial {}: k1_j and k_u_j should differ",
            trial
        );

        let gamma_j = ScalarField::rand(&mut rng);
        let oprf_state = OPRFState { gamma_j, k1_j };

        let (user_msg, mut local_state) =
            user_prepare_message(&x, &sid, &ssid, &pp, k_u_j, &mut rng);

        let tagger_msg = tagger_process(&user_msg, &k_tag, &oprf_state, &sid, &ssid, &pp, &mut rng)
            .expect("tagger_process should succeed");

        let f_j = user_oprf_eval(&mut local_state, &mut rng);
        let f_prime_j = tagger_oprf_complete(&f_j, &gamma_j);

        let result = user_complete(&local_state, &tagger_msg, &f_prime_j, &user_msg);
        assert!(
            result.is_none(),
            "Trial {}: user_complete should return None when keys mismatch (k={})",
            trial, kappa
        );
    }
}

#[test]
fn test_kbs_oprf_key_agreement() {
    let mut rng = StdRng::seed_from_u64(5555);

    for trial in 0..NUM_TRIALS {
        let gamma = ScalarField::rand(&mut rng);
        let k = G1::rand(&mut rng); // shared key k1 == ku
        let s = ScalarField::rand(&mut rng); // user blinding

        let k_bytes = g1_to_bytes(&k);

        // Tagger side: rho_T = H_2(k || H_1(k) * gamma)
        let h1_k = h1_oprf(&k_bytes);
        let h1_k_gamma = h1_k * gamma;
        let mut rho_t_input = k_bytes.clone();
        rho_t_input.extend_from_slice(&g1_to_bytes(&h1_k_gamma));
        let rho_t = h2_oprf(&rho_t_input);

        // User side: f = H_1(k) * s, then f' = f * gamma, then f'/s = H_1(k) * gamma
        let f = h1_k * s;
        let f_prime = f * gamma; // tagger_oprf_complete
        let s_inv = s.inverse().expect("s must be non-zero");
        let oprf_output = f_prime * s_inv; // = H_1(k) * gamma

        let mut rho_u_input = k_bytes.clone();
        rho_u_input.extend_from_slice(&g1_to_bytes(&oprf_output));
        let rho_u = h2_oprf(&rho_u_input);

        assert_eq!(
            rho_t, rho_u,
            "Trial {}: rho_T and rho_U must agree when keys match",
            trial
        );
    }
}
