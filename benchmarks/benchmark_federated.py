#!/usr/bin/env python3
"""
Federated Learning Benchmark Script for PUDA Protocol
Generates professional-quality graphs for academic presentations.

This script runs benchmarks with realistic FL parameters:
- 10-100 clients (typical FL deployment)
- Vector dimensions: 10-100 (simulating gradient aggregation)
- 16-bit integer values (quantized gradients)
"""

import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns
from pathlib import Path
import time
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Benchmark parameters for Federated Learning scenario
FL_CONFIG = {
    'users': [10, 25, 50, 75, 100],       # Number of FL clients
    'dimensions': [10, 25, 50, 75, 100],  # Vector dimension (gradient size proxy)
    'trials': 5,                           # Trials per configuration
    'max_value': 650,                      # Max value per element (adjusted for DLP table)
}

# Plot style configuration
STYLE_CONFIG = {
    'figure_dpi': 150,
    'font_family': 'sans-serif',
    'title_size': 14,
    'label_size': 12,
    'tick_size': 10,
    'legend_size': 10,
}

# Modern color palette (inspired by Tailwind CSS)
COLORS = {
    'blue': '#3B82F6',
    'purple': '#8B5CF6',
    'pink': '#EC4899',
    'green': '#22C55E',
    'orange': '#F97316',
    'cyan': '#06B6D4',
    'red': '#EF4444',
    'gray': '#6B7280',
    'light_gray': '#F3F4F6',
    'dark': '#1F2937',
}

# Metric labels and colors
METRICS = {
    'AvgSetup(ms)': {'label': 'Setup', 'color': COLORS['blue'], 'marker': 'o'},
    'AvgEnc(ms)': {'label': 'Encryption', 'color': COLORS['orange'], 'marker': 's'},
    'AvgAgg(ms)': {'label': 'Aggregation', 'color': COLORS['green'], 'marker': '^'},
    'AvgVerify(ms)': {'label': 'Verification', 'color': COLORS['red'], 'marker': 'D'},
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def setup_plot_style():
    """Configure matplotlib for professional plots."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.edgecolor': COLORS['gray'],
        'axes.labelcolor': COLORS['dark'],
        'text.color': COLORS['dark'],
        'xtick.color': COLORS['dark'],
        'ytick.color': COLORS['dark'],
        'grid.color': '#E5E7EB',
        'grid.linestyle': '--',
        'grid.alpha': 0.7,
        'font.family': STYLE_CONFIG['font_family'],
        'font.size': STYLE_CONFIG['tick_size'],
        'axes.titlesize': STYLE_CONFIG['title_size'],
        'axes.labelsize': STYLE_CONFIG['label_size'],
        'legend.fontsize': STYLE_CONFIG['legend_size'],
        'figure.dpi': STYLE_CONFIG['figure_dpi'],
    })

def run_benchmark(num_users, kappa, max_value, trials):
    """Run a single benchmark configuration."""
    # Adjust max_value for DLP table constraint
    safe_max = min(max_value, 65535 // num_users - 1)

    # Get script directory for relative paths
    script_dir = Path(__file__).parent.resolve()
    binary = script_dir / '..' / 'puda-rust' / 'target' / 'release' / 'puda'

    cmd = [
        str(binary),
        '--num-users', str(num_users),
        '--kappa', str(kappa),
        '--min-value', '0',
        '--max-value', str(safe_max),
        '--number-of-trials', str(trials),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(script_dir))
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        print(f"Error: Binary not found at {binary}. Run 'cargo build --release' first.")
        return False

def run_all_benchmarks():
    """Run all benchmark configurations."""
    print("=" * 60)
    print("   PUDA Benchmark - Federated Learning Configuration")
    print("=" * 60)
    print(f"\nClients (N):     {FL_CONFIG['users']}")
    print(f"Dimensions (κ):  {FL_CONFIG['dimensions']}")
    print(f"Trials:          {FL_CONFIG['trials']}")
    print(f"Max value:       {FL_CONFIG['max_value']}")
    print("\n" + "-" * 60)

    # Check if binary exists
    script_dir = Path(__file__).parent.resolve()
    binary_path = script_dir / '..' / 'puda-rust' / 'target' / 'release' / 'puda'
    if not binary_path.exists():
        print("\nCompiling Rust project...")
        rust_dir = script_dir / '..' / 'puda-rust'
        subprocess.run(['cargo', 'build', '--release'], check=True, cwd=str(rust_dir))

    total = len(FL_CONFIG['users']) * len(FL_CONFIG['dimensions'])
    current = 0
    start_time = time.time()

    # Clear existing results
    csv_path = Path('benchmark_results.csv')
    if csv_path.exists():
        csv_path.unlink()

    for kappa in FL_CONFIG['dimensions']:
        for n in FL_CONFIG['users']:
            current += 1
            safe_max = min(FL_CONFIG['max_value'], 65535 // n - 1)
            print(f"[{current:3d}/{total}] N={n:3d}, κ={kappa:3d}, max={safe_max:4d} ... ", end='', flush=True)

            success = run_benchmark(n, kappa, FL_CONFIG['max_value'], FL_CONFIG['trials'])
            print("✓" if success else "✗")

    elapsed = time.time() - start_time
    print("-" * 60)
    print(f"Completed in {elapsed:.1f}s")
    print("=" * 60)

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def create_performance_line_plot(df, x_col, fixed_col, fixed_val, title, xlabel, filename):
    """Create a professional line plot."""
    fig, ax = plt.subplots(figsize=(10, 6))

    subset = df[df[fixed_col] == fixed_val].sort_values(by=x_col)

    for metric, props in METRICS.items():
        if metric in subset.columns:
            ax.plot(subset[x_col], subset[metric],
                   marker=props['marker'],
                   color=props['color'],
                   linewidth=2.5,
                   markersize=8,
                   label=props['label'],
                   markeredgecolor='white',
                   markeredgewidth=1.5)

    ax.set_xlabel(xlabel, fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(title, fontweight='bold', pad=15)

    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=False,
              edgecolor=COLORS['gray'], facecolor='white')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(filename, dpi=STYLE_CONFIG['figure_dpi'], bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_scalability_comparison(df, filename):
    """Create side-by-side scalability comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Aggregation vs Users
    kappa_max = df['Kappa'].max()
    subset = df[df['Kappa'] == kappa_max].sort_values('NumUsers')

    ax = axes[0]
    ax.plot(subset['NumUsers'], subset['AvgAgg(ms)'],
           marker='o', color=COLORS['green'], linewidth=2.5, markersize=8,
           label='Aggregation', markeredgecolor='white', markeredgewidth=1.5)
    ax.plot(subset['NumUsers'], subset['AvgVerify(ms)'],
           marker='s', color=COLORS['red'], linewidth=2.5, markersize=8,
           label='Verification', markeredgecolor='white', markeredgewidth=1.5)

    ax.set_xlabel('Number of Clients (N)', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(f'Scalability vs. Clients (κ={kappa_max})', fontweight='bold', pad=10)
    ax.legend(frameon=True, fancybox=True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add annotation for constant time verification
    ax.annotate('Nearly constant!',
               xy=(subset['NumUsers'].iloc[-1], subset['AvgVerify(ms)'].iloc[-1]),
               xytext=(subset['NumUsers'].iloc[-1] - 20, subset['AvgVerify(ms)'].iloc[-1] + 20),
               fontsize=10, color=COLORS['red'],
               arrowprops=dict(arrowstyle='->', color=COLORS['red'], lw=1.5))

    # Right: Encryption vs Dimension
    n_max = df['NumUsers'].max()
    subset = df[df['NumUsers'] == n_max].sort_values('Kappa')

    ax = axes[1]
    ax.plot(subset['Kappa'], subset['AvgEnc(ms)'],
           marker='s', color=COLORS['orange'], linewidth=2.5, markersize=8,
           label='Encryption', markeredgecolor='white', markeredgewidth=1.5)
    ax.plot(subset['Kappa'], subset['AvgSetup(ms)'],
           marker='o', color=COLORS['blue'], linewidth=2.5, markersize=8,
           label='Setup', markeredgecolor='white', markeredgewidth=1.5)

    ax.set_xlabel('Vector Dimension (κ)', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(f'Scalability vs. Dimension (N={n_max})', fontweight='bold', pad=10)
    ax.legend(frameon=True, fancybox=True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(filename, dpi=STYLE_CONFIG['figure_dpi'], bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_heatmap_grid(df, filename):
    """Create professional heatmap grid."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    cmap = sns.color_palette("YlOrRd", as_cmap=True)

    metrics_order = ['AvgSetup(ms)', 'AvgEnc(ms)', 'AvgAgg(ms)', 'AvgVerify(ms)']

    for idx, metric in enumerate(metrics_order):
        row, col = divmod(idx, 2)
        ax = axes[row, col]

        pivot = df.pivot_table(values=metric, index='Kappa', columns='NumUsers', aggfunc='mean')

        sns.heatmap(pivot, ax=ax, annot=True, fmt='.1f', cmap=cmap,
                   cbar_kws={'label': 'Time (ms)', 'shrink': 0.8},
                   annot_kws={'size': 9},
                   linewidths=0.5, linecolor='white')

        ax.set_title(METRICS[metric]['label'], fontweight='bold', pad=10, fontsize=12)
        ax.set_xlabel('Number of Clients (N)', fontweight='bold')
        ax.set_ylabel('Vector Dimension (κ)', fontweight='bold')
        ax.invert_yaxis()

    fig.suptitle('Performance Heatmaps - Federated Learning Configuration',
                fontweight='bold', fontsize=14, y=1.02)

    plt.tight_layout()
    plt.savefig(filename, dpi=STYLE_CONFIG['figure_dpi'], bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_bar_comparison(df, filename):
    """Create bar chart comparing operation times."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get data for a specific configuration
    n_mid = df['NumUsers'].median()
    k_mid = df['Kappa'].median()
    subset = df[(df['NumUsers'] == n_mid) & (df['Kappa'] == k_mid)]

    if subset.empty:
        # Fallback to max values
        n_max = df['NumUsers'].max()
        k_max = df['Kappa'].max()
        subset = df[(df['NumUsers'] == n_max) & (df['Kappa'] == k_max)]

    metrics_order = ['AvgSetup(ms)', 'AvgEnc(ms)', 'AvgAgg(ms)', 'AvgVerify(ms)']
    values = [subset[m].values[0] for m in metrics_order]
    labels = [METRICS[m]['label'] for m in metrics_order]
    colors = [METRICS[m]['color'] for m in metrics_order]

    bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=2)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
               f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(f'Operation Comparison (N={int(subset["NumUsers"].values[0])}, κ={int(subset["Kappa"].values[0])})',
                fontweight='bold', pad=15)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(filename, dpi=STYLE_CONFIG['figure_dpi'], bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

def create_complexity_analysis(df, filename):
    """Create complexity analysis visualization."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Verification time vs N (should be ~constant)
    ax = axes[0]
    kappa_max = df['Kappa'].max()
    subset = df[df['Kappa'] == kappa_max].sort_values('NumUsers')

    ax.scatter(subset['NumUsers'], subset['AvgVerify(ms)'],
              color=COLORS['red'], s=100, zorder=5, edgecolors='white', linewidths=2)

    # Fit line
    z = np.polyfit(subset['NumUsers'], subset['AvgVerify(ms)'], 1)
    p = np.poly1d(z)
    ax.plot(subset['NumUsers'], p(subset['NumUsers']),
           color=COLORS['red'], linestyle='--', alpha=0.7, linewidth=2,
           label=f'Linear fit (slope={z[0]:.3f})')

    # Horizontal line for constant reference
    mean_val = subset['AvgVerify(ms)'].mean()
    ax.axhline(y=mean_val, color=COLORS['green'], linestyle=':', linewidth=2,
              label=f'Mean = {mean_val:.1f} ms')

    ax.set_xlabel('Number of Clients (N)', fontweight='bold')
    ax.set_ylabel('Verification Time (ms)', fontweight='bold')
    ax.set_title('Verification Complexity Analysis', fontweight='bold', pad=10)
    ax.legend(frameon=True, fancybox=True, loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Right: All operations complexity
    ax = axes[1]
    n_max = df['NumUsers'].max()
    subset = df[df['NumUsers'] == n_max].sort_values('Kappa')

    for metric, props in METRICS.items():
        if metric in subset.columns:
            ax.scatter(subset['Kappa'], subset[metric],
                      color=props['color'], s=100, marker=props['marker'],
                      edgecolors='white', linewidths=2, label=props['label'])

            # Fit and plot trend line
            z = np.polyfit(subset['Kappa'], subset[metric], 1)
            p = np.poly1d(z)
            ax.plot(subset['Kappa'], p(subset['Kappa']),
                   color=props['color'], linestyle='--', alpha=0.5, linewidth=1.5)

    ax.set_xlabel('Vector Dimension (κ)', fontweight='bold')
    ax.set_ylabel('Time (ms)', fontweight='bold')
    ax.set_title(f'Scaling with Dimension (N={n_max})', fontweight='bold', pad=10)
    ax.legend(frameon=True, fancybox=True, loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(filename, dpi=STYLE_CONFIG['figure_dpi'], bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  ✓ Saved: {filename}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    setup_plot_style()

    # Check if we should run benchmarks
    csv_path = Path('benchmark_results.csv')

    run_benchmarks = True
    if csv_path.exists():
        print("\nExisting benchmark_results.csv found.")
        response = input("Run new benchmarks? (y/N): ").strip().lower()
        run_benchmarks = response == 'y'

    if run_benchmarks:
        run_all_benchmarks()

    # Load results
    print("\n" + "=" * 60)
    print("   Generating Professional Graphs")
    print("=" * 60 + "\n")

    try:
        df = pd.read_csv('benchmark_results.csv')
        df.columns = df.columns.str.strip()
        print(f"Loaded {len(df)} data points\n")
    except FileNotFoundError:
        print("Error: benchmark_results.csv not found. Run benchmarks first.")
        return

    # Generate all graphs
    print("Creating visualizations...")

    # 1. Performance vs Dimension
    kappa_max = df['Kappa'].max()
    n_max = df['NumUsers'].max()

    create_performance_line_plot(
        df, 'Kappa', 'NumUsers', n_max,
        f'Performance vs. Vector Dimension (N={n_max} clients)',
        'Vector Dimension (κ)',
        'graph_impact_kappa.png'
    )

    # 2. Performance vs Users
    create_performance_line_plot(
        df, 'NumUsers', 'Kappa', kappa_max,
        f'Performance vs. Number of Clients (κ={kappa_max})',
        'Number of Clients (N)',
        'graph_impact_users.png'
    )

    # 3. Scalability comparison
    create_scalability_comparison(df, 'graph_scalability.png')

    # 4. Heatmaps
    create_heatmap_grid(df, 'graph_heatmaps.png')

    # 5. Bar comparison
    create_bar_comparison(df, 'graph_bar_comparison.png')

    # 6. Complexity analysis
    create_complexity_analysis(df, 'graph_complexity.png')

    print("\n" + "=" * 60)
    print("   All graphs generated successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
