use super::models::*;
use super::utils::*;

/// 1. Setup
pub fn setup(
    num_users: usize, 
    rng: &mut StdRng, 
    kappa: usize, 
) -> (PublicParams, Vec<UserSecretKey>, AggregatorSecretKey, DataDealerVK) {

    // getting P_1 and P_2
    let p_1 = G1::generator();
    let p_2 = G2::generator();
    
    let mut user_keys = Vec::new();

    // a = (a_1, ..., a_k) sampled uniformly from Z^{k}_{q}
    let a: Vec<ScalarField> = (0..kappa)
        .map(|_| ScalarField::rand(rng))
        .collect();

    // we construct vk_a with the vector a and we initialize vk_b
    let vk_a: Vec<G2> = a.iter()
        .map(|a_value| p_2 * a_value)
        .collect();
    
    // initialisation of vk_b
    let mut vk_b: Vec<G2> = vec![G2::zero(); num_users];
    
    // we initialize ak
    let mut ak: ScalarField = ScalarField::zero();
    
    // for each user we generate/construct a encryption-key and a tag-key
    for i in 0..num_users {
        // we generate ek_i
        let ek_i = ScalarField::rand(rng);
        ak += ek_i;
        
        // we generate b_i, contruct tk_i and vk_b
        let b_i = ScalarField::rand(rng);

        let tk_i = (a.clone(), b_i);
        vk_b[i] = p_2 * b_i;

        user_keys.push(UserSecretKey {
            id: i,
            ek: ek_i,
            tk: tk_i,
        });
    }

    let aggregator_key = AggregatorSecretKey {
        ska: -ak,
    };

    let verification_key = DataDealerVK {
        vk_a, vk_b,
    };
    
    let pp = PublicParams { p_1, p_2 };

    (pp, user_keys, aggregator_key, verification_key)
}


/// 3. Aggregation
pub fn aggregate(
    agg_sk: &AggregatorSecretKey,
    inputs: &[CiphertextAndTag],
    tau: u64,
    kappa: usize,
    _pp: &PublicParams,
) -> (Vec<u64>, G1) {
    // 1. compute V an X
    let mut x: Vec<u64> = Vec::new();

    for k in 0..kappa{
        // we compute H(tau||kappa)
        let tau_kappa = format!("{}{}", tau, k);
        let h = map_to_group(&tau_kappa);

        // set the value of the k-th row of V
        let mut v = G1::zero();
        for ct in inputs {
            v += ct.c[k];
        }
        v += h * agg_sk.ska;

        x.push(find_discrete_log(v));
    }

    // 2. compute gamma
    let mut gamma = G1::zero();
    for ct in inputs {
        gamma += ct.sigma;
    }

    (x, gamma)
}