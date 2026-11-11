use super::models::*;
use super::utils::*;

/// 4. Verification
pub fn verify(
    data_vk: &DataDealerVK,
    gamma: G1,
    x_tau: Vec<u64>, //vector of the aggregation
    tau: u64,
    kappa: usize,
    pp: &PublicParams,
) -> bool {
    let g1_gen = pp.p_1;
    let g2_gen = pp.p_2;

    // left part of the equality test
    let lhs = Bls12_381::pairing(gamma, g2_gen).0;

    // right part of the equality test
    let mut rhs = <Bls12_381 as Pairing>::TargetField::one();
    for k in 0..kappa{
        rhs *= Bls12_381::pairing(g1_gen * ScalarField::from(x_tau[k]), data_vk.vk_a[k]).0;
    }
    for i in 0..data_vk.vk_b.len(){
        rhs *= Bls12_381::pairing(map_to_group(&tau.to_string()), data_vk.vk_b[i]).0;
    }

    lhs == rhs
}