use super::models::*;
use std::collections::HashMap;
use std::sync::OnceLock;
use ark_serialize::CanonicalSerialize;

/// Maximum supported value for discrete log recovery (2^16).
/// Aggregated sums must be strictly less than this value.
const DLP_TABLE_SIZE: u64 = 65536;

/// Precomputed discrete log lookup table (lazily initialized).
static DLP_LOOKUP_TABLE: OnceLock<HashMap<Vec<u8>, u64>> = OnceLock::new();

/// Initializes the discrete log lookup table.
///
/// Precomputes g^i for i in [0, DLP_TABLE_SIZE) and stores them in a HashMap
/// for O(1) discrete log recovery. This is the standard approach for small
/// exponents in pairing-based cryptography.
fn init_dlp_lookup_table() -> HashMap<Vec<u8>, u64> {
    eprintln!("[PUDA] Initializing discrete log lookup table ({} entries)...", DLP_TABLE_SIZE);

    let g1_gen = G1::generator();
    let mut table = HashMap::with_capacity(DLP_TABLE_SIZE as usize);
    let mut current = G1::zero();

    for i in 0..DLP_TABLE_SIZE {
        let mut bytes = Vec::new();
        current.serialize_compressed(&mut bytes).expect("Serialization failed");
        table.insert(bytes, i);
        current += g1_gen;
    }

    eprintln!("[PUDA] Discrete log lookup table ready ({} entries).", table.len());
    table
}

/// Returns a reference to the discrete log lookup table, initializing it if necessary.
fn get_dlp_lookup_table() -> &'static HashMap<Vec<u8>, u64> {
    DLP_LOOKUP_TABLE.get_or_init(init_dlp_lookup_table)
}

/// Hash function H': {0,1}* -> Fq x {0,1}
/// Based on the GLS paper (Section 3.2).
fn h_prime(input: &[u8]) -> (Fq, u8) {
    let hash = Sha512::digest(input);
    let x_coordinate = Fq::from_be_bytes_mod_order(&hash);
    let sign_bit = (hash[63] & 1) as u8;
    (x_coordinate, sign_bit)
}

/// Maps an arbitrary string to a point in G1.
///
/// Implements the hash-to-curve construction from GLS (Section 3.2).
/// Uses try-and-increment to find a valid curve point.
pub fn map_to_group(message: &str) -> G1 {
    let one_over_delta = 1024.0_f64;
    let max_iterations = (one_over_delta).log2().log2().ceil() as usize;
    let mut counter = 0u64;

    loop {
        if counter >= (1u64 << max_iterations) {
            panic!("map_to_group: exceeded maximum iterations");
        }

        let input_str = format!("{:0width$b}{}", counter, message, width = max_iterations);
        let (x, sign_selector) = h_prime(input_str.as_bytes());

        let coeff_a = <g1::Config as SWCurveConfig>::COEFF_A;
        let coeff_b = <g1::Config as SWCurveConfig>::COEFF_B;

        // Compute f(x) = x^3 + ax + b
        let f_x = x.pow([3]) + coeff_a * x + coeff_b;

        if f_x.legendre().is_qr() {
            // x is a valid x-coordinate, compute y
            let root_a = f_x.sqrt().unwrap();
            let root_b = -root_a;

            let a_big = root_a.into_bigint();
            let b_big = root_b.into_bigint();

            let (y_0, y_1) = if a_big < b_big {
                (root_a, root_b)
            } else {
                (root_b, root_a)
            };

            let y_chosen = if sign_selector == 0 { y_0 } else { y_1 };
            let point_candidate = G1Affine::new_unchecked(x, y_chosen);
            let point_projective = point_candidate.into_group();

            // Multiply by cofactor to ensure point is in the correct subgroup
            let cofactor_limbs = <g1::Config as CurveConfig>::COFACTOR;
            let mut cofactor_big = BigInteger384::default();
            for (idx, &limb) in cofactor_limbs.iter().enumerate() {
                if idx < cofactor_big.0.len() {
                    cofactor_big.0[idx] = limb;
                }
            }

            let final_point = point_projective.mul_bigint(cofactor_big);

            if !final_point.is_zero() {
                return final_point;
            }
        }

        counter += 1;
    }
}

/// Recovers the discrete logarithm of a G1 point using the precomputed lookup table.
///
/// Given a point P = g^x, returns x if x is in [0, 65535].
/// Panics if the discrete log is not found (value out of range).
///
/// Time complexity: O(1) lookup after initial table construction.
pub fn find_discrete_log(target: G1) -> u64 {
    let table = get_dlp_lookup_table();

    let mut bytes = Vec::new();
    target.serialize_compressed(&mut bytes).expect("Serialization failed");

    match table.get(&bytes) {
        Some(&value) => value,
        None => panic!("Discrete log not found: aggregated sum exceeds {} or is negative", DLP_TABLE_SIZE - 1),
    }
}