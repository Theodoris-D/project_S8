use puda::puda::models::*;
use puda::puda::utils::map_to_group;
use ark_serialize::{CanonicalSerialize, CanonicalDeserialize};
use sha2::{Sha256, Digest};
use aes_gcm::{aead::{Aead, KeyInit}, Aes256Gcm, Nonce};

// ============================================================================
// DATA STRUCTURES
// ============================================================================

#[derive(Clone)]
pub struct ProofRU {
    // Dummy field 
    pub dummy: G1,
}

#[derive(Clone)]
pub struct ProofRT {
    // Dummy field 
    pub dummy: G1,
}

#[derive(Clone)]
pub struct TaggerKey {
    pub a_j: Vec<ScalarField>,
    pub b_j: ScalarField,
}

#[derive(Clone)]
pub struct OPRFState {
    pub gamma_j: ScalarField,
    pub k1_j: G1,
}

/// Message User
#[derive(Clone)]
pub struct UserMessage {
    pub c_j: Vec<G1>,
    pub d_j: G1,
    pub proof_u: ProofRU,
    pub r_j: ScalarField, 
}

/// Message Tagger
pub struct TaggerMessage {
    pub ciphertext: Vec<u8>,
    pub nonce: [u8; 12],
    pub h1_gamma: G1,
}


/// ===================================================================
/// Round 1: USER
/// ===================================================================

fn generate_proof_ru(_x: &ScalarField, _r_j: &ScalarField, _c_j: &G1, _d_j: &G1,
                     _sid: &str, _ssid: &str, _pp: &PublicParams) -> ProofRU {
    ProofRU { dummy: G1::zero() }
}

pub fn user_prepare_message(
    x: &Vec<ScalarField>,
    sid: &str,
    ssid: &str,
    pp: &PublicParams,
    rng: &mut StdRng,
) -> UserMessage {
    // Line 7: Pick r_j <-$ Z_q, compute (c_j, d_j) <- ([x]_1, H(sid||ssid)) * r_j
    let r_j = ScalarField::rand(rng);
    let x_in_g1 = pp.p_1 * x;
    let c_j: Vec<G1> = x.iter()
        .map(|x_k| (pp.p_1 * x_k) * r_j)
        .collect();

    let h_sid_ssid = map_to_group(&format!("{}{}", sid, ssid));
    let d_j = h_sid_ssid * r_j;

    // Line 8: Prove pi_{U,j} for R_U
    let proof_u = generate_proof_ru(x, &r_j, &c_j, &d_j, sid, ssid, pp);

    // Line 11: Prepare (c_j, d_j, pi_{U,j}) for tagger
    UserMessage { c_j, d_j, proof_u, r_j }
}

/// ===================================================================
/// Round 1: TAGGER
/// ===================================================================

fn verify_proof_ru(_proof: &ProofRU, _c_j: &G1, _d_j: &G1,
                   _sid: &str, _ssid: &str, _pp: &PublicParams) -> bool {
    // Dummy verification
    true
}
fn generate_proof_rt(_c_j: &G1, _d_j: &G1, _e_j: &G1, _k_tag: &TaggerKey) -> ProofRT {
    // Dummy proof 
    ProofRT { dummy: G1::zero() }
}



pub fn tagger_process(
    user_msg: &UserMessage,
    k_tag: &TaggerKey,
    oprf_state: &OPRFState,
    sid: &str,
    ssid: &str,
    pp: &PublicParams,
    rng: &mut StdRng,
) -> Option<TaggerMessage> {
    // Line 12: Verify pi_{U,j}
    if !verify_proof_ru(&user_msg.proof_u, &user_msg.c_j, &user_msg.d_j, sid, ssid, pp) {
        return None; 
    }

    // Ligne 14: Compute e_j <- c_j * a_j^T + d_j * b_j
    let mut e_j = G1::zero();
    for (c_jk, a_jk) in user_msg.c_j.iter().zip(&k_tag.a_j) {
        e_j += *c_jk * a_jk;
    }
    e_j += user_msg.d_j * k_tag.b_j;

    // Line 15: Prove pi_{T,j} for R_T
    let proof_t = generate_proof_rt(&user_msg.c_j, &user_msg.d_j, &e_j, k_tag);

    // Line 16: rho_{T,j} <- H_2(k1_j || H_1(k1_j) * gamma_j)
    // TODO

    // Line 17: Encrypt cptx1_j <- Enc(rho_{T,j}, e_j || pi_{T,j})
    // TODO
    // Line 20: Return message to user
    Some(TaggerMessage { ciphertext, nonce: nonce_bytes, h1_gamma })
}

// ============================================================================
// ROUND 2: User
// ============================================================================

/// Line 27: Compute f'_j <- f_j * gamma_j
pub fn tagger_oprf_complete(f_j: &G1, gamma_j: &ScalarField) -> G1 {
    *f_j * gamma_j
}

fn verify_proof_rt(_proof: &ProofRT, _c_j: &G1, _d_j: &G1, _e_j: &G1) -> bool {
    // Dummy 
    true
}



// ============================================================================
// MAIN
// ============================================================================
fn main() {}