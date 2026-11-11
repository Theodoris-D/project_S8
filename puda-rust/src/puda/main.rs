use puda::puda::user::enc_tag;
use puda::puda::data_aggregator::{aggregate, setup};
use puda::puda::data_analyzer::verify;

use clap::Parser;
use ark_std::rand::{rngs::StdRng, SeedableRng, Rng};
use std::time::{Instant, Duration};
use std::fs::OpenOptions;
use std::io::Write;

#[derive(Parser, Debug)]
#[command(author, version, about = "PUDA - Private User Data Aggregation Protocol")]
struct Args {
    /// Enable verbose output for demonstration
    #[arg(short, long, default_value_t = false)]
    demo: bool,

    /// Vector dimension (kappa)
    #[arg(short, long, default_value_t = 2)]
    kappa: usize,

    /// Number of participating users
    #[arg(short, long, default_value_t = 7)]
    num_users: usize,

    /// Minimum value for generated user data
    #[arg(long, default_value_t = 0)]
    min_value: u64,

    /// Maximum value for generated user data
    #[arg(short, long, default_value_t = 20)]
    max_value: u64,

    /// Number of trials for averaging results
    #[arg(short = 't', long, default_value_t = 1)]
    number_of_trials: usize,

    /// Use random seed (default: deterministic)
    #[arg(short, long, default_value_t = false)]
    random_seed: bool,
}

fn main() {
    let args = Args::parse();

    // Conditional logging macro (only prints in demo mode)
    macro_rules! log {
        ($($arg:tt)*) => {
            if args.demo {
                println!($($arg)*);
            }
        }
    }

    if args.demo {
        println!("========================================");
        println!("         PUDA Protocol - Demo Mode");
        println!("========================================\n");
    } else {
        println!("[PUDA] Benchmark mode: {} trial(s)", args.number_of_trials);
        println!("[PUDA] Config: n={}, k={}, range=[{}, {}]",
                 args.num_users, args.kappa, args.min_value, args.max_value);
    }

    let mut total_setup_time = Duration::new(0, 0);
    let mut total_enc_time = Duration::new(0, 0);
    let mut total_agg_time = Duration::new(0, 0);
    let mut total_verify_time = Duration::new(0, 0);

    let mut rng = if args.random_seed {
        StdRng::from_entropy()
    } else {
        StdRng::seed_from_u64(0u64)
    };

    let tau: u64 = 123456;

    for trial in 1..=args.number_of_trials {
        if !args.demo {
            print!("\r[PUDA] Trial {}/{}...", trial, args.number_of_trials);
            std::io::stdout().flush().unwrap();
        }

        // Phase 1: Setup
        log!("[1/4] Setup phase...");
        let start = Instant::now();
        let (pp, user_keys, aggregator_key, verification_key) = setup(args.num_users, &mut rng, args.kappa);
        total_setup_time += start.elapsed();
        log!("      Setup complete.\n");

        // Generate user data (not timed - simulation only)
        let mut user_data = Vec::new();
        for i in 0..args.num_users {
            let data_vec: Vec<u64> = (0..args.kappa)
                .map(|_| args.min_value + rng.gen::<u64>() % (args.max_value - args.min_value))
                .collect();
            log!("      User {} data: {:?}", i, data_vec);
            user_data.push(data_vec);
        }

        // Phase 2: Encryption
        log!("\n[2/4] Encryption phase...");
        let start = Instant::now();
        let user_inputs: Vec<_> = (0..args.num_users)
            .map(|i| enc_tag(&user_keys[i], user_data[i].clone(), tau, args.kappa, &pp))
            .collect();
        total_enc_time += start.elapsed();
        log!("      All users encrypted their data.\n");

        // Phase 3: Aggregation
        log!("[3/4] Aggregation phase...");
        let start = Instant::now();
        let (sum, gamma) = aggregate(&aggregator_key, &user_inputs, tau, args.kappa, &pp);
        total_agg_time += start.elapsed();
        log!("      Aggregated sum: {:?}\n", sum);

        // Phase 4: Verification
        log!("[4/4] Verification phase...");
        let start = Instant::now();
        let is_valid = verify(&verification_key, gamma.clone(), sum.clone(), tau, args.kappa, &pp);
        total_verify_time += start.elapsed();

        if is_valid {
            log!("      Result: VALID\n");
        } else {
            log!("      Result: INVALID\n");
        }

        // Falsification test (demo mode only)
        if args.demo {
            log!("--- Falsification Test ---");
            let mut fake_sum = sum.clone();
            if !fake_sum.is_empty() { fake_sum[0] += 1; } else { fake_sum.push(999); }
            log!("    Tampered sum: {:?}", fake_sum);
            let is_fake_valid = verify(&verification_key, gamma, fake_sum, tau, args.kappa, &pp);
            if !is_fake_valid {
                log!("    Result: Correctly rejected (fraud detected)\n");
            } else {
                log!("    Result: ERROR - Should have been rejected!\n");
            }
        }
    }

    if !args.demo {
        let avg_setup = total_setup_time.as_micros() as f64 / args.number_of_trials as f64 / 1000.0;
        let avg_enc = total_enc_time.as_micros() as f64 / args.number_of_trials as f64 / 1000.0;
        let avg_agg = total_agg_time.as_micros() as f64 / args.number_of_trials as f64 / 1000.0;
        let avg_ver = total_verify_time.as_micros() as f64 / args.number_of_trials as f64 / 1000.0;

        println!("\n\n[PUDA] Results (averaged over {} trials):", args.number_of_trials);
        println!("       Setup:        {:>8.4} ms", avg_setup);
        println!("       Encryption:   {:>8.4} ms ({} users)", avg_enc, args.num_users);
        println!("       Aggregation:  {:>8.4} ms", avg_agg);
        println!("       Verification: {:>8.4} ms", avg_ver);

        // Save results to CSV
        let file_path = "benchmark_results.csv";
        let file_exists = std::path::Path::new(file_path).exists();

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)
            .unwrap();

        if !file_exists {
            writeln!(file, "Kappa,NumUsers,MaxValue,Trials,AvgSetup(ms),AvgEnc(ms),AvgAgg(ms),AvgVerify(ms)").unwrap();
        }

        writeln!(
            file,
            "{},{},{},{},{:.4},{:.4},{:.4},{:.4}",
            args.kappa, args.num_users, args.max_value, args.number_of_trials,
            avg_setup, avg_enc, avg_agg, avg_ver
        ).unwrap();

        println!("[PUDA] Results appended to '{}'", file_path);
    }
}