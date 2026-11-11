pub use ark_bls12_381::{Bls12_381, Fr as ScalarField, Fq, G1Affine, G1Projective as G1, G2Projective as G2, g1};
pub use ark_ec::{short_weierstrass::SWCurveConfig, pairing::Pairing, Group, AffineRepr, CurveConfig}; 
pub use ark_ff::{Field, PrimeField, BigInteger384, One}; 
pub use ark_std::rand::{rngs::StdRng, SeedableRng, Rng};
pub use ark_std::{UniformRand, Zero};
pub use sha2::{Digest, Sha512};

// Structure of public parameters
#[derive(Clone)]
#[allow(dead_code)]
#[warn(non_snake_case)]
pub struct PublicParams {
    pub p_1: G1,
    pub p_2: G2,
}

// Structure of the user's keys
#[derive(Clone)]
#[allow(dead_code)]
pub struct UserSecretKey {
    pub id: usize,
    pub ek:  ScalarField,
    pub tk: (Vec<ScalarField>, ScalarField),
}

// Structure of the agregator's secret key
#[derive(Clone)]
pub struct AggregatorSecretKey {
    pub ska: ScalarField,
}

#[derive(Clone)]
pub struct DataDealerVK {
    pub vk_a: Vec<G2>,
    pub vk_b: Vec<G2>,
}

// Data of an encrypted tag
#[derive(Clone)]
pub struct CiphertextAndTag {
    pub c: Vec<G1>,
    pub sigma: G1,
}

