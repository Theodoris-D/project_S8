use super::models::*;
use super::utils::*;

/// 2. EncTag
pub fn enc_tag(
    uk: &UserSecretKey, 
    x_i: Vec<u64>,      
    tau: u64,           
    kappa: usize,       
    pp: &PublicParams
) -> CiphertextAndTag {
    
    // 1. Compute c_i
    let mut c: Vec<G1> = vec![G1::zero(); kappa];

    for k in 0..kappa {
        // we compute H(tau||kappa)
        let tau_kappa = format!("{}{}", tau, k);
        let h = map_to_group(&tau_kappa);
        
        // set the value of the k-th row of c_i.
        c[k] = pp.p_1 * ScalarField::from(x_i[k]) + h * uk.ek;
    }

    // 2. Compute the tag
    // sigma = H(tau) * b_i + Sum(a_k * x_k) * P1
    
    // Part 1: b_i * H(tau) -> uk.tk.1 is b_i
    let h_tau = map_to_group(&tau.to_string());
    let mut sigma = h_tau * uk.tk.1; 
    
    // Part 2: Sum(a_k * x_k * P1)
    // uk.tk.0 is the vector a
    for (k, x_val) in x_i.iter().enumerate() {
        if k < uk.tk.0.len() {
            let a_k = uk.tk.0[k];
            // Multiply : P1 * (x_k * a_k)
            sigma += pp.p_1 * (ScalarField::from(*x_val) * a_k);
        }
    }
    
    CiphertextAndTag { c, sigma }
}