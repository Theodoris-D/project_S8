#!/usr/bin/env python3
"""
Comprehensive PUDA Benchmark Script
Analyzes all aspects of the protocol under different conditions.

Generates:
1. Impact of n (users) with fixed kappa
2. Impact of kappa (dimensions) with fixed n
3. Impact of value size
4. Per-phase analysis
5. Stress tests with maximum values
"""

import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
import time
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================

# Directory setup
SCRIPT_DIR = Path(__file__).parent.resolve()
RUST_DIR = SCRIPT_DIR / '..' / 'puda-rust'
BINARY = RUST_DIR / 'target' / 'release' / 'puda'
OUTPUT_DIR = SCRIPT_DIR / '..' / 'presentation' / 'figures'

# Plot style
COLORS = {
    'setup': '#3B82F6',      # Blue
    'encryption': '#F97316', # Orange
    'aggregation': '#22C55E', # Green
    'verification': '#EF4444', # Red
    'total': '#8B5CF6',      # Purple
}

# ============================================================================
# BENCHMARK FUNCTIONS
# ============================================================================

def ensure_binary():
    """Compile if needed."""
    if not BINARY.exists():
        print("Compiling Rust project...")
        subprocess.run(['cargo', 'build', '--release'], check=True, cwd=str(RUST_DIR))
    return BINARY.exists()

def run_single_benchmark(n, kappa, max_val, trials=3):
    """Run a single benchmark and return results."""
    cmd = [
        str(BINARY),
        '--num-users', str(n),
        '--kappa', str(kappa),
        '--min-value', '0',
        '--max-value', str(max_val),
        '--number-of-trials', str(trials),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(SCRIPT_DIR))
        if result.returncode == 0:
            # Parse CSV output
            csv_path = SCRIPT_DIR / 'benchmark_results.csv'
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                if len(df) > 0:
                    last_row = df.iloc[-1]
                    return {
                        'n': n,
                        'kappa': kappa,
                        'max_val': max_val,
                        'setup_ms': last_row['AvgSetup(ms)'],
                        'enc_ms': last_row['AvgEnc(ms)'],
                        'agg_ms': last_row['AvgAgg(ms)'],
                        'verify_ms': last_row['AvgVerify(ms)'],
                    }
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def benchmark_varying_n(kappa_fixed=50, n_values=None, max_val=500, trials=3):
    """Benchmark with varying number of users."""
    if n_values is None:
        n_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    print(f"\n{'='*60}")
    print(f"  Benchmark: Varying N (users) with κ={kappa_fixed}")
    print(f"{'='*60}")

    results = []
    for n in n_values:
        safe_max = min(max_val, 65535 // n - 1)
        print(f"  N={n:3d}, κ={kappa_fixed}, max={safe_max}...", end=' ', flush=True)
        r = run_single_benchmark(n, kappa_fixed, safe_max, trials)
        if r:
            results.append(r)
            print(f"✓ (enc={r['enc_ms']:.0f}ms)")
        else:
            print("✗")

    return pd.DataFrame(results)

def benchmark_varying_kappa(n_fixed=50, kappa_values=None, max_val=500, trials=3):
    """Benchmark with varying dimensions."""
    if kappa_values is None:
        kappa_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    print(f"\n{'='*60}")
    print(f"  Benchmark: Varying κ (dimensions) with N={n_fixed}")
    print(f"{'='*60}")

    safe_max = min(max_val, 65535 // n_fixed - 1)

    results = []
    for kappa in kappa_values:
        print(f"  N={n_fixed}, κ={kappa:3d}, max={safe_max}...", end=' ', flush=True)
        r = run_single_benchmark(n_fixed, kappa, safe_max, trials)
        if r:
            results.append(r)
            print(f"✓ (enc={r['enc_ms']:.0f}ms)")
        else:
            print("✗")

    return pd.DataFrame(results)

def benchmark_value_impact(n=50, kappa=50, trials=3):
    """Test if value size affects performance."""
    print(f"\n{'='*60}")
    print(f"  Benchmark: Value Size Impact (N={n}, κ={kappa})")
    print(f"{'='*60}")

    safe_max = 65535 // n - 1
    # Test different value ranges
    value_ranges = [
        (0, 10),
        (0, 100),
        (0, safe_max // 2),
        (0, safe_max),
    ]

    results = []
    for min_v, max_v in value_ranges:
        print(f"  Values in [{min_v}, {max_v}]...", end=' ', flush=True)

        cmd = [
            str(BINARY),
            '--num-users', str(n),
            '--kappa', str(kappa),
            '--min-value', str(min_v),
            '--max-value', str(max_v),
            '--number-of-trials', str(trials),
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(SCRIPT_DIR))
            csv_path = SCRIPT_DIR / 'benchmark_results.csv'
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                if len(df) > 0:
                    last = df.iloc[-1]
                    results.append({
                        'min_val': min_v,
                        'max_val': max_v,
                        'range': f"[{min_v},{max_v}]",
                        'setup_ms': last['AvgSetup(ms)'],
                        'enc_ms': last['AvgEnc(ms)'],
                        'agg_ms': last['AvgAgg(ms)'],
                        'verify_ms': last['AvgVerify(ms)'],
                    })
                    print(f"✓ (enc={last['AvgEnc(ms)']:.0f}ms)")
        except Exception as e:
            print(f"✗ ({e})")

    return pd.DataFrame(results)

def benchmark_stress_test(trials=3):
    """Stress test with maximum configurations."""
    print(f"\n{'='*60}")
    print(f"  Benchmark: Stress Test (Maximum Configurations)")
    print(f"{'='*60}")

    # Maximum configurations that fit in DLP table
    configs = [
        (100, 100, 655),   # 100 users, 100 dims, max=655
        (50, 200, 1310),   # 50 users, 200 dims
        (200, 50, 327),    # 200 users, 50 dims
        (25, 100, 2621),   # 25 users, larger values
        (10, 100, 6553),   # 10 users, even larger values
    ]

    results = []
    for n, kappa, max_v in configs:
        print(f"  N={n:3d}, κ={kappa:3d}, max={max_v}...", end=' ', flush=True)
        r = run_single_benchmark(n, kappa, max_v, trials)
        if r:
            results.append(r)
            total = r['setup_ms'] + r['enc_ms'] + r['agg_ms'] + r['verify_ms']
            print(f"✓ (total={total:.0f}ms)")
        else:
            print("✗")

    return pd.DataFrame(results)

def benchmark_full_grid(trials=3):
    """Full grid benchmark for heatmaps."""
    print(f"\n{'='*60}")
    print(f"  Benchmark: Full Grid (for heatmaps)")
    print(f"{'='*60}")

    n_vals = [10, 25, 50, 75, 100]
    kappa_vals = [10, 25, 50, 75, 100]

    results = []
    total = len(n_vals) * len(kappa_vals)
    current = 0

    for n in n_vals:
        for kappa in kappa_vals:
            current += 1
            safe_max = min(650, 65535 // n - 1)
            print(f"  [{current:2d}/{total}] N={n:3d}, κ={kappa:3d}...", end=' ', flush=True)
            r = run_single_benchmark(n, kappa, safe_max, trials)
            if r:
                results.append(r)
                print("✓")
            else:
                print("✗")

    return pd.DataFrame(results)

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def setup_style():
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 11,
        'legend.fontsize': 9,
        'figure.dpi': 150,
    })

def plot_varying_n(df, output_path):
    """Plot performance vs number of users."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: All phases
    ax = axes[0]
    ax.plot(df['n'], df['setup_ms'], 'o-', color=COLORS['setup'], label='Setup', linewidth=2, markersize=6)
    ax.plot(df['n'], df['enc_ms'], 's-', color=COLORS['encryption'], label='Encryption', linewidth=2, markersize=6)
    ax.plot(df['n'], df['agg_ms'], '^-', color=COLORS['aggregation'], label='Aggregation', linewidth=2, markersize=6)
    ax.plot(df['n'], df['verify_ms'], 'D-', color=COLORS['verification'], label='Verification', linewidth=2, markersize=6)

    ax.set_xlabel('Number of Users (N)', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(f'All Phases vs. Users (κ={df["kappa"].iloc[0]})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Right: Aggregation focus (should be ~constant)
    ax = axes[1]
    ax.plot(df['n'], df['agg_ms'], 'o-', color=COLORS['aggregation'], linewidth=2.5, markersize=8)

    mean_agg = df['agg_ms'].mean()
    ax.axhline(y=mean_agg, color='gray', linestyle='--', label=f'Mean = {mean_agg:.1f} ms')

    ax.set_xlabel('Number of Users (N)', fontweight='bold')
    ax.set_ylabel('Aggregation Time (ms)', fontweight='bold')
    ax.set_title('Aggregation Time (nearly constant due to O(1) DLP lookup)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def plot_varying_kappa(df, output_path):
    """Plot performance vs dimension."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: All phases
    ax = axes[0]
    ax.plot(df['kappa'], df['setup_ms'], 'o-', color=COLORS['setup'], label='Setup', linewidth=2, markersize=6)
    ax.plot(df['kappa'], df['enc_ms'], 's-', color=COLORS['encryption'], label='Encryption', linewidth=2, markersize=6)
    ax.plot(df['kappa'], df['agg_ms'], '^-', color=COLORS['aggregation'], label='Aggregation', linewidth=2, markersize=6)
    ax.plot(df['kappa'], df['verify_ms'], 'D-', color=COLORS['verification'], label='Verification', linewidth=2, markersize=6)

    ax.set_xlabel('Vector Dimension (κ)', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(f'All Phases vs. Dimension (N={df["n"].iloc[0]})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Right: Encryption focus (dominates)
    ax = axes[1]
    ax.plot(df['kappa'], df['enc_ms'], 's-', color=COLORS['encryption'], linewidth=2.5, markersize=8)

    # Linear fit
    z = np.polyfit(df['kappa'], df['enc_ms'], 1)
    p = np.poly1d(z)
    ax.plot(df['kappa'], p(df['kappa']), '--', color='gray', label=f'Linear fit (slope={z[0]:.1f} ms/dim)')

    ax.set_xlabel('Vector Dimension (κ)', fontweight='bold')
    ax.set_ylabel('Encryption Time (ms)', fontweight='bold')
    ax.set_title('Encryption Time (O(κ) - linear in dimension)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def plot_value_impact(df, output_path):
    """Plot impact of value size."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Bar chart
    ax = axes[0]
    x = range(len(df))
    width = 0.2

    ax.bar([i - 1.5*width for i in x], df['setup_ms'], width, label='Setup', color=COLORS['setup'])
    ax.bar([i - 0.5*width for i in x], df['enc_ms'], width, label='Encryption', color=COLORS['encryption'])
    ax.bar([i + 0.5*width for i in x], df['agg_ms'], width, label='Aggregation', color=COLORS['aggregation'])
    ax.bar([i + 1.5*width for i in x], df['verify_ms'], width, label='Verification', color=COLORS['verification'])

    ax.set_xlabel('Value Range', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title('Performance vs. Value Range', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df['range'], rotation=15)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Right: Relative difference
    ax = axes[1]
    baseline = df.iloc[0]

    for col, color, label in [
        ('setup_ms', COLORS['setup'], 'Setup'),
        ('enc_ms', COLORS['encryption'], 'Encryption'),
        ('agg_ms', COLORS['aggregation'], 'Aggregation'),
        ('verify_ms', COLORS['verification'], 'Verification'),
    ]:
        relative = (df[col] / baseline[col] - 1) * 100
        ax.plot(range(len(df)), relative, 'o-', color=color, label=label, linewidth=2, markersize=6)

    ax.axhline(y=0, color='gray', linestyle='--')
    ax.set_xlabel('Value Range', fontweight='bold')
    ax.set_ylabel('Relative Change (%)', fontweight='bold')
    ax.set_title('Relative Change from Baseline (small values)', fontweight='bold')
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['range'], rotation=15)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def plot_stress_test(df, output_path):
    """Plot stress test results."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Stacked bar chart
    configs = [f"N={r['n']}, κ={r['kappa']}\nmax={r['max_val']}" for _, r in df.iterrows()]

    bottom = np.zeros(len(df))

    for col, color, label in [
        ('setup_ms', COLORS['setup'], 'Setup'),
        ('enc_ms', COLORS['encryption'], 'Encryption'),
        ('agg_ms', COLORS['aggregation'], 'Aggregation'),
        ('verify_ms', COLORS['verification'], 'Verification'),
    ]:
        ax.bar(configs, df[col], bottom=bottom, label=label, color=color)
        bottom += df[col].values

    # Add total time labels
    for i, (_, row) in enumerate(df.iterrows()):
        total = row['setup_ms'] + row['enc_ms'] + row['agg_ms'] + row['verify_ms']
        ax.text(i, total + 200, f'{total:.0f}ms', ha='center', fontweight='bold')

    ax.set_xlabel('Configuration', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title('Stress Test: Total Time Breakdown', fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def plot_heatmaps(df, output_path):
    """Create heatmaps for each phase."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    phases = [
        ('setup_ms', 'Setup', axes[0, 0]),
        ('enc_ms', 'Encryption', axes[0, 1]),
        ('agg_ms', 'Aggregation', axes[1, 0]),
        ('verify_ms', 'Verification', axes[1, 1]),
    ]

    for col, title, ax in phases:
        pivot = df.pivot_table(values=col, index='kappa', columns='n', aggfunc='mean')
        sns.heatmap(pivot, ax=ax, annot=True, fmt='.0f', cmap='YlOrRd',
                   cbar_kws={'label': 'Time (ms)'})
        ax.set_title(f'{title} Time (ms)', fontweight='bold')
        ax.set_xlabel('Number of Users (N)', fontweight='bold')
        ax.set_ylabel('Dimension (κ)', fontweight='bold')
        ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def plot_per_user_encryption(df, output_path):
    """Plot encryption time per user."""
    fig, ax = plt.subplots(figsize=(10, 6))

    df_copy = df.copy()
    df_copy['enc_per_user'] = df_copy['enc_ms'] / df_copy['n']

    # Group by kappa
    for kappa in df_copy['kappa'].unique():
        subset = df_copy[df_copy['kappa'] == kappa].sort_values('n')
        ax.plot(subset['n'], subset['enc_per_user'], 'o-', label=f'κ={kappa}', linewidth=2, markersize=6)

    ax.set_xlabel('Number of Users (N)', fontweight='bold')
    ax.set_ylabel('Encryption Time per User (ms)', fontweight='bold')
    ax.set_title('Encryption Time per User (should be constant in N)', fontweight='bold')
    ax.legend(title='Dimension')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def plot_complexity_analysis(df, output_path):
    """Analyze complexity of each phase."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Setup vs n (should be O(n))
    ax = axes[0, 0]
    kappa_fixed = df['kappa'].max()
    subset = df[df['kappa'] == kappa_fixed].sort_values('n')
    ax.scatter(subset['n'], subset['setup_ms'], s=80, color=COLORS['setup'])
    z = np.polyfit(subset['n'], subset['setup_ms'], 1)
    ax.plot(subset['n'], np.poly1d(z)(subset['n']), '--', color='gray', label=f'Linear: {z[0]:.2f}n + {z[1]:.1f}')
    ax.set_xlabel('N')
    ax.set_ylabel('Setup (ms)')
    ax.set_title(f'Setup Complexity (κ={kappa_fixed})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Encryption vs kappa (should be O(kappa))
    ax = axes[0, 1]
    n_fixed = df['n'].max()
    subset = df[df['n'] == n_fixed].sort_values('kappa')
    ax.scatter(subset['kappa'], subset['enc_ms'], s=80, color=COLORS['encryption'])
    z = np.polyfit(subset['kappa'], subset['enc_ms'], 1)
    ax.plot(subset['kappa'], np.poly1d(z)(subset['kappa']), '--', color='gray', label=f'Linear: {z[0]:.1f}κ + {z[1]:.1f}')
    ax.set_xlabel('κ')
    ax.set_ylabel('Encryption (ms)')
    ax.set_title(f'Encryption Complexity (N={n_fixed})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Aggregation vs n (should be nearly constant due to DLP)
    ax = axes[1, 0]
    subset = df[df['kappa'] == kappa_fixed].sort_values('n')
    ax.scatter(subset['n'], subset['agg_ms'], s=80, color=COLORS['aggregation'])
    mean_val = subset['agg_ms'].mean()
    ax.axhline(y=mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.1f}ms')
    ax.set_xlabel('N')
    ax.set_ylabel('Aggregation (ms)')
    ax.set_title(f'Aggregation Complexity (κ={kappa_fixed}) - Nearly O(1)!', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Verification vs (n + kappa)
    ax = axes[1, 1]
    df_copy = df.copy()
    df_copy['n_plus_kappa'] = df_copy['n'] + df_copy['kappa']
    ax.scatter(df_copy['n_plus_kappa'], df_copy['verify_ms'], s=80, color=COLORS['verification'])
    z = np.polyfit(df_copy['n_plus_kappa'], df_copy['verify_ms'], 1)
    x_fit = np.linspace(df_copy['n_plus_kappa'].min(), df_copy['n_plus_kappa'].max(), 100)
    ax.plot(x_fit, np.poly1d(z)(x_fit), '--', color='gray', label=f'Linear: {z[0]:.2f}(n+κ) + {z[1]:.1f}')
    ax.set_xlabel('N + κ')
    ax.set_ylabel('Verification (ms)')
    ax.set_title('Verification Complexity - O(n + κ)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_path}")

def create_summary_table(df_grid, output_path):
    """Create summary statistics."""
    summary = []

    for _, row in df_grid.iterrows():
        total = row['setup_ms'] + row['enc_ms'] + row['agg_ms'] + row['verify_ms']
        summary.append({
            'N': int(row['n']),
            'κ': int(row['kappa']),
            'Setup (ms)': f"{row['setup_ms']:.1f}",
            'Encryption (ms)': f"{row['enc_ms']:.1f}",
            'Aggregation (ms)': f"{row['agg_ms']:.1f}",
            'Verification (ms)': f"{row['verify_ms']:.1f}",
            'Total (ms)': f"{total:.1f}",
        })

    df_summary = pd.DataFrame(summary)
    df_summary.to_csv(output_path, index=False)
    print(f"  Saved: {output_path}")

    # Also print
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    print(df_summary.to_string(index=False))

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*60)
    print("  PUDA Comprehensive Benchmark Suite")
    print("="*60)

    if not ensure_binary():
        print("Error: Could not compile Rust project")
        return

    setup_style()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Varying N
    print("\n[1/6] Benchmarking varying N...")
    df_n = benchmark_varying_n(kappa_fixed=50, n_values=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], trials=3)
    if len(df_n) > 0:
        plot_varying_n(df_n, OUTPUT_DIR / 'bench_varying_n.png')

    # 2. Varying kappa
    print("\n[2/6] Benchmarking varying κ...")
    df_kappa = benchmark_varying_kappa(n_fixed=50, kappa_values=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], trials=3)
    if len(df_kappa) > 0:
        plot_varying_kappa(df_kappa, OUTPUT_DIR / 'bench_varying_kappa.png')

    # 3. Value impact
    print("\n[3/6] Testing value size impact...")
    df_values = benchmark_value_impact(n=50, kappa=50, trials=3)
    if len(df_values) > 0:
        plot_value_impact(df_values, OUTPUT_DIR / 'bench_value_impact.png')

    # 4. Stress test
    print("\n[4/6] Running stress tests...")
    df_stress = benchmark_stress_test(trials=3)
    if len(df_stress) > 0:
        plot_stress_test(df_stress, OUTPUT_DIR / 'bench_stress_test.png')

    # 5. Full grid
    print("\n[5/6] Running full grid benchmark...")
    df_grid = benchmark_full_grid(trials=3)
    if len(df_grid) > 0:
        plot_heatmaps(df_grid, OUTPUT_DIR / 'bench_heatmaps.png')
        plot_per_user_encryption(df_grid, OUTPUT_DIR / 'bench_enc_per_user.png')
        plot_complexity_analysis(df_grid, OUTPUT_DIR / 'bench_complexity.png')
        create_summary_table(df_grid, OUTPUT_DIR / 'bench_summary.csv')

    # 6. Copy key graphs
    print("\n[6/6] Creating presentation graphs...")

    # Rename for presentation
    import shutil
    renames = [
        ('bench_varying_n.png', 'graph_impact_users.png'),
        ('bench_varying_kappa.png', 'graph_impact_kappa.png'),
        ('bench_heatmaps.png', 'graph_heatmaps.png'),
        ('bench_complexity.png', 'graph_scalability.png'),
    ]

    for src, dst in renames:
        src_path = OUTPUT_DIR / src
        dst_path = OUTPUT_DIR / dst
        if src_path.exists():
            shutil.copy(src_path, dst_path)
            print(f"  Copied: {src} -> {dst}")

    print("\n" + "="*60)
    print("  Benchmark Complete!")
    print("="*60)
    print(f"\nGraphs saved to: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
