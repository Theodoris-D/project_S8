use super::models::*;
use super::utils::map_to_group;
use ark_serialize::{CanonicalSerialize, CanonicalDeserialize};
use sha2::{Sha256, Digest};
use aes_gcm::{aead::{Aead, KeyInit}, Aes256Gcm, Nonce};

// ============================================================================
// HELPER FUNCTIONS (OPRF / 2HashDH)
// ============================================================================

/// H_1: Hash to Group (2HashDH OPRF [31])
/// Reuses map_to_group which implements hash-to-curve (GLS Section 3.2).
pub fn h1_oprf(data: &[u8]) -> G1 {
    map_to_group(&hex::encode(data))
}

/// H_2: Hash to symmetric key (2HashDH OPRF [31])
/// Returns a 256-bit key for AES-GCM.
pub fn h2_oprf(data: &[u8]) -> [u8; 32] {
    let hash = Sha256::digest(data);
    let mut key = [0u8; 32];
    key.copy_from_slice(&hash);
    key
}

/// Serialize a G1 point to compressed bytes.
pub fn g1_to_bytes(point: &G1) -> Vec<u8> {
    let mut bytes = Vec::new();
    point.serialize_compressed(&mut bytes).expect("Serialization failed");
    bytes
}

// ============================================================================
// DATA STRUCTURES
// ============================================================================

#[derive(Clone)]
pub struct ProofRU {
    pub dummy: G1,
}

#[derive(Clone)]
pub struct ProofRT {
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

/// Message sent from User to Tagger (r_j is NOT included - kept locally)
#[derive(Clone)]
pub struct UserMessage {
    pub c_j: Vec<G1>,
    pub d_j: G1,
    pub proof_u: ProofRU,
}

/// Local state kept by the User (never sent to the tagger)
#[derive(Clone)]
pub struct UserLocalState {
    pub r_j: ScalarField,   // blinding factor (line 7)
    pub s_j: ScalarField,   // OPRF blinding (line 25)
    pub k_u_j: G1,          // key from CMP (line 22)
}

/// Message sent from Tagger to User
pub struct TaggerMessage {
    pub ciphertext: Vec<u8>,   // cptx^1_j
    pub nonce: [u8; 12],
    pub h1_gamma: G1,          // H_1(k^1_j) * gamma_j (for OPRF)
}


/// ===================================================================
/// Round 1: USER
/// ===================================================================

fn generate_proof_ru(_x: &[ScalarField], _r_j: &ScalarField, _c_j: &[G1], _d_j: &G1,
                     _sid: &str, _ssid: &str, _pp: &PublicParams) -> ProofRU {
    ProofRU { dummy: G1::zero() }
}

pub fn user_prepare_message(
    x: &[ScalarField],
    sid: &str,
    ssid: &str,
    pp: &PublicParams,
    k_u_j: G1,
    rng: &mut StdRng,
) -> (UserMessage, UserLocalState) {
    // Line 7: Pick r_j <-$ Z_q, compute (c_j, d_j) <- ([x]_1, H(sid||ssid)) * r_j
    let r_j = ScalarField::rand(rng);
    let c_j: Vec<G1> = x.iter()
        .map(|x_k| (pp.p_1 * x_k) * r_j)
        .collect();

    let h_sid_ssid = map_to_group(&format!("{}||{}", sid, ssid));
    let d_j = h_sid_ssid * r_j;

    // Line 8: Prove pi_{U,j} for R_U
    let proof_u = generate_proof_ru(x, &r_j, &c_j, &d_j, sid, ssid, pp);

    // Line 11: Prepare (c_j, d_j, pi_{U,j}) for tagger
    let msg = UserMessage { c_j, d_j, proof_u };
    let local_state = UserLocalState {
        r_j,
        s_j: ScalarField::zero(), // will be set in user_oprf_eval
        k_u_j,
    };
    (msg, local_state)
}

/// ===================================================================
/// Round 1: TAGGER
/// ===================================================================

fn verify_proof_ru(_proof: &ProofRU, _c_j: &[G1], _d_j: &G1,
                   _sid: &str, _ssid: &str, _pp: &PublicParams) -> bool {
    // Dummy verification
    true
}

fn generate_proof_rt(_c_j: &[G1], _d_j: &G1, _e_j: &G1, _k_tag: &TaggerKey) -> ProofRT {
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

    // Line 14: Compute e_j <- c_j * a_j^T + d_j * b_j
    let mut e_j = G1::zero();
    for (c_jk, a_jk) in user_msg.c_j.iter().zip(&k_tag.a_j) {
        e_j += *c_jk * a_jk;
    }
    e_j += user_msg.d_j * k_tag.b_j;

    // Line 15: Prove pi_{T,j} for R_T
    let proof_t = generate_proof_rt(&user_msg.c_j, &user_msg.d_j, &e_j, k_tag);

    // Line 16: rho_{T,j} <- H_2(k^1_j || H_1(k^1_j) * gamma_j)
    let k1_bytes = g1_to_bytes(&oprf_state.k1_j);
    let h1_k1 = h1_oprf(&k1_bytes);
    let h1_k1_gamma = h1_k1 * oprf_state.gamma_j;

    let mut rho_input = k1_bytes.clone();
    rho_input.extend_from_slice(&g1_to_bytes(&h1_k1_gamma));
    let rho_t_j = h2_oprf(&rho_input);

    // Line 17: cptx^1_j <- Enc(rho_{T,j}, e_j || pi_{T,j})
    let key = aes_gcm::Key::<Aes256Gcm>::from_slice(&rho_t_j);
    let cipher = Aes256Gcm::new(key);
    let nonce_bytes: [u8; 12] = rng.gen();
    let nonce = Nonce::from_slice(&nonce_bytes);

    let mut plaintext = g1_to_bytes(&e_j);
    let proof_bytes = g1_to_bytes(&proof_t.dummy); // dummy proof serialization
    plaintext.extend_from_slice(&proof_bytes);

    let ciphertext = cipher.encrypt(nonce, plaintext.as_ref())
        .expect("encryption failed");

    // Line 20: Return message to user
    Some(TaggerMessage { ciphertext, nonce: nonce_bytes, h1_gamma: h1_k1_gamma })
}

// ============================================================================
// ROUND 2: User OPRF
// ============================================================================

/// Lines 25-26: User computes f_j and sends it to the tagger
pub fn user_oprf_eval(
    state: &mut UserLocalState,
    rng: &mut StdRng,
) -> G1 {
    // Line 25: f_j <- H_1(k_{U,j}) * s_j
    let k_u_bytes = g1_to_bytes(&state.k_u_j);
    let h1_k_u = h1_oprf(&k_u_bytes);
    state.s_j = ScalarField::rand(rng);
    let f_j = h1_k_u * state.s_j;
    // Line 26: send f_j to T_j
    f_j
}

/// Line 27: Tagger computes f'_j <- f_j * gamma_j
pub fn tagger_oprf_complete(f_j: &G1, gamma_j: &ScalarField) -> G1 {
    *f_j * gamma_j
}

fn verify_proof_rt(_proof: &ProofRT, _c_j: &[G1], _d_j: &G1, _e_j: &G1) -> bool {
    // Dummy
    true
}

// ============================================================================
// ROUND 2: User Output (Lines 28a-d)
// ============================================================================

/// Lines 28(a)-(d): User completes the protocol
pub fn user_complete(
    state: &UserLocalState,
    tagger_msg: &TaggerMessage,    // cptx^1_j from round 1
    f_prime_j: &G1,                // f'_j from round 2 (line 27)
    user_msg: &UserMessage,        // c_j, d_j for verification
) -> Option<G1> {
    // Line 28(a): rho_{U,j} <- H_2(k_{U,j} || f'_j / s_j)
    let s_j_inv = state.s_j.inverse().expect("s_j must be non-zero");
    let oprf_output = *f_prime_j * s_j_inv; // f'_j / s_j = H_1(k_{U,j})^{gamma_j}

    let mut rho_input = g1_to_bytes(&state.k_u_j);
    rho_input.extend_from_slice(&g1_to_bytes(&oprf_output));
    let rho_u_j = h2_oprf(&rho_input);

    // Line 28(b): Decrypt (e_j || pi_{T,j}) <- Dec(rho_{U,j}, cptx^1_j)
    let key = aes_gcm::Key::<Aes256Gcm>::from_slice(&rho_u_j);
    let cipher = Aes256Gcm::new(key);
    let nonce = Nonce::from_slice(&tagger_msg.nonce);

    let plaintext = cipher.decrypt(nonce, tagger_msg.ciphertext.as_ref())
        .ok()?; // returns None if decryption fails (key mismatch)

    // Parse e_j from plaintext (first 48 bytes for compressed G1)
    let e_j = G1::deserialize_compressed(&plaintext[..48])
        .ok()?;

    // Line 28(c): Verify V((c, d, e_j), pi_{T,j}) = 1
    let _proof_bytes = &plaintext[48..];
    if !verify_proof_rt(&ProofRT { dummy: G1::zero() }, &user_msg.c_j, &user_msg.d_j, &e_j) {
        return None;
    }

    // Line 28(d): sigma^1_j <- e_j / r
    let r_inv = state.r_j.inverse().expect("r_j must be non-zero");
    let sigma_1_j = e_j * r_inv;

    Some(sigma_1_j)
}
