use clap::Parser;
use std::process::Command;
use std::time::Instant;

#[derive(Parser, Debug)]
#[command(author, version, about = "PUDA Protocol - Automated Benchmark Runner")]
struct BenchArgs {
    /// Number of trials per configuration (results are averaged)
    #[arg(long, default_value_t = 10)]
    number_of_trials: usize,

    /// Minimum value for generated user data
    #[arg(long, default_value_t = 0)]
    min_value: u64,

    /// Maximum value for generated user data (constraint: num_users * max_value < 65536)
    #[arg(long, default_value_t = 500)]
    max_value: u64,

    /// Maximum number of users to benchmark
    #[arg(long, default_value_t = 100)]
    max_users: usize,

    /// Maximum vector dimension (kappa) to benchmark
    #[arg(long, default_value_t = 10)]
    max_kappa: usize,

    /// Number of measurement points for users (X-axis)
    #[arg(long, default_value_t = 5)]
    number_of_x: usize,

    /// Number of measurement points for kappa (Y-axis)
    #[arg(long, default_value_t = 3)]
    number_of_y: usize,

    /// Generate graphs automatically after benchmark (requires Python)
    #[arg(long, default_value_t = true)]
    generate_graphs: bool,
}

fn main() {
    let args = BenchArgs::parse();

    // Validate constraint: aggregated sum must fit in lookup table (< 65536)
    let max_safe_value = 65535 / args.max_users as u64;
    let effective_max_value = if args.max_value > max_safe_value {
        eprintln!("[WARN] max_value adjusted: {} -> {} (constraint: num_users * max_value < 65536)",
                  args.max_value, max_safe_value);
        max_safe_value
    } else {
        args.max_value
    };

    println!("========================================");
    println!("       PUDA Benchmark Runner");
    println!("========================================");
    println!("Configuration:");
    println!("  Trials per config : {}", args.number_of_trials);
    println!("  Data range        : [{}, {}]", args.min_value, effective_max_value);
    println!("  Users             : 1 to {} ({} points)", args.max_users, args.number_of_x);
    println!("  Kappa             : 1 to {} ({} points)", args.max_kappa, args.number_of_y);
    println!("========================================\n");

    // Compile in release mode
    println!("[1/3] Compiling project (release mode)...");
    let status = Command::new("cargo")
        .args(["build", "--release"])
        .status()
        .expect("Failed to execute cargo build");

    if !status.success() {
        eprintln!("[ERROR] Compilation failed. Aborting.");
        return;
    }
    println!("[1/3] Compilation complete.\n");

    // Generate parameter grid
    let user_steps = generate_steps(1, args.max_users, args.number_of_x);
    let kappa_steps = generate_steps(1, args.max_kappa, args.number_of_y);

    let total_iterations = user_steps.len() * kappa_steps.len();
    let mut current_iter = 0;
    let global_start = Instant::now();

    println!("[2/3] Running {} benchmark configurations...\n", total_iterations);

    for &kappa in &kappa_steps {
        for &num_users in &user_steps {
            current_iter += 1;

            // Adjust max_value for this configuration
            let safe_max_value = std::cmp::min(
                effective_max_value,
                65535 / num_users as u64
            );

            print!("  [{:3}/{}] n={:4}, k={:2}, max={:5} ... ",
                   current_iter, total_iterations, num_users, kappa, safe_max_value);
            std::io::Write::flush(&mut std::io::stdout()).unwrap();

            let binary_path = if cfg!(windows) {
                "target/release/puda.exe"
            } else {
                "target/release/puda"
            };

            let output = Command::new(binary_path)
                .arg("--num-users")
                .arg(num_users.to_string())
                .arg("--kappa")
                .arg(kappa.to_string())
                .arg("--min-value")
                .arg(args.min_value.to_string())
                .arg("--max-value")
                .arg(safe_max_value.to_string())
                .arg("--number-of-trials")
                .arg(args.number_of_trials.to_string())
                .output()
                .expect("Failed to execute puda binary");

            if !output.status.success() {
                println!("FAILED");
                eprintln!("    Error: {}", String::from_utf8_lossy(&output.stderr).trim());
            } else {
                println!("OK");
            }
        }
    }

    let duration = global_start.elapsed();
    println!("\n[2/3] Benchmarks complete. Duration: {:.2?}", duration);
    println!("      Results saved to: benchmark_results.csv");

    // Generate graphs
    if args.generate_graphs {
        println!("\n[3/3] Generating graphs...");
        let python_status = Command::new("python3")
            .arg("../benchmarks/analyze_result.py")
            .status();

        match python_status {
            Ok(status) if status.success() => {
                println!("[3/3] Graphs generated successfully.");
            }
            Ok(_) => {
                eprintln!("[WARN] Graph generation failed. Install dependencies: pip install pandas matplotlib seaborn scipy");
            }
            Err(e) => {
                eprintln!("[WARN] Python not found: {}. Skipping graph generation.", e);
            }
        }
    } else {
        println!("\n[3/3] Graph generation skipped (--generate-graphs=false)");
    }

    println!("\n========================================");
    println!("            Benchmark Complete");
    println!("========================================");
}

/// Generates evenly spaced values between min and max (inclusive).
/// Similar to numpy.linspace.
fn generate_steps(min: usize, max: usize, count: usize) -> Vec<usize> {
    if count == 0 { return vec![]; }
    if count == 1 { return vec![max]; }

    let step_size = (max - min) as f64 / (count - 1) as f64;
    let mut steps: Vec<usize> = (0..count)
        .map(|i| ((min as f64 + i as f64 * step_size).round() as usize).max(1))
        .collect();

    steps.dedup();
    steps
}