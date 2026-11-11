#!/usr/bin/env python3
"""
Generate comprehensive graphs from existing benchmark data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
CSV_PATH = SCRIPT_DIR / 'benchmark_results.csv'
OUTPUT_DIR = SCRIPT_DIR / '..' / 'presentation' / 'figures'

# Colors
COLORS = {
    'setup': '#3B82F6',
    'encryption': '#F97316',
    'aggregation': '#22C55E',
    'verification': '#EF4444',
}

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

def load_data():
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    # Rename for easier access
    df = df.rename(columns={
        'Kappa': 'kappa',
        'NumUsers': 'n',
        'MaxValue': 'max_val',
        'Trials': 'trials',
        'AvgSetup(ms)': 'setup_ms',
        'AvgEnc(ms)': 'enc_ms',
        'AvgAgg(ms)': 'agg_ms',
        'AvgVerify(ms)': 'verify_ms',
    })
    return df

# ============================================================================
# GRAPH 1: Impact of N (users) with fixed kappa
# ============================================================================
def plot_impact_n(df, output_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    kappa_values = sorted(df['kappa'].unique())

    # Top-left: All phases for kappa=100
    ax = axes[0, 0]
    kappa = 100
    subset = df[df['kappa'] == kappa].sort_values('n')
    ax.plot(subset['n'], subset['setup_ms'], 'o-', color=COLORS['setup'], label='Setup', lw=2)
    ax.plot(subset['n'], subset['enc_ms'], 's-', color=COLORS['encryption'], label='Encryption', lw=2)
    ax.plot(subset['n'], subset['agg_ms'], '^-', color=COLORS['aggregation'], label='Aggregation', lw=2)
    ax.plot(subset['n'], subset['verify_ms'], 'D-', color=COLORS['verification'], label='Verification', lw=2)
    ax.set_xlabel('Number of Users (N)')
    ax.set_ylabel('Time (ms)')
    ax.set_title(f'All Phases vs N (κ={kappa})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Top-right: Aggregation for different kappas (should be nearly constant)
    ax = axes[0, 1]
    for kappa in kappa_values:
        subset = df[df['kappa'] == kappa].sort_values('n')
        ax.plot(subset['n'], subset['agg_ms'], 'o-', label=f'κ={kappa}', lw=2, markersize=5)
    ax.set_xlabel('Number of Users (N)')
    ax.set_ylabel('Aggregation Time (ms)')
    ax.set_title('Aggregation vs N (nearly constant!)', fontweight='bold')
    ax.legend(title='Dimension')
    ax.grid(True, alpha=0.3)

    # Bottom-left: Setup for different kappas
    ax = axes[1, 0]
    for kappa in kappa_values:
        subset = df[df['kappa'] == kappa].sort_values('n')
        ax.plot(subset['n'], subset['setup_ms'], 'o-', label=f'κ={kappa}', lw=2, markersize=5)
    ax.set_xlabel('Number of Users (N)')
    ax.set_ylabel('Setup Time (ms)')
    ax.set_title('Setup vs N', fontweight='bold')
    ax.legend(title='Dimension')
    ax.grid(True, alpha=0.3)

    # Bottom-right: Verification for different kappas
    ax = axes[1, 1]
    for kappa in kappa_values:
        subset = df[df['kappa'] == kappa].sort_values('n')
        ax.plot(subset['n'], subset['verify_ms'], 'o-', label=f'κ={kappa}', lw=2, markersize=5)
    ax.set_xlabel('Number of Users (N)')
    ax.set_ylabel('Verification Time (ms)')
    ax.set_title('Verification vs N', fontweight='bold')
    ax.legend(title='Dimension')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")

# ============================================================================
# GRAPH 2: Impact of kappa (dimension) with fixed N
# ============================================================================
def plot_impact_kappa(df, output_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    n_values = sorted(df['n'].unique())

    # Top-left: All phases for n=100
    ax = axes[0, 0]
    n = 100
    subset = df[df['n'] == n].sort_values('kappa')
    ax.plot(subset['kappa'], subset['setup_ms'], 'o-', color=COLORS['setup'], label='Setup', lw=2)
    ax.plot(subset['kappa'], subset['enc_ms'], 's-', color=COLORS['encryption'], label='Encryption', lw=2)
    ax.plot(subset['kappa'], subset['agg_ms'], '^-', color=COLORS['aggregation'], label='Aggregation', lw=2)
    ax.plot(subset['kappa'], subset['verify_ms'], 'D-', color=COLORS['verification'], label='Verification', lw=2)
    ax.set_xlabel('Dimension (κ)')
    ax.set_ylabel('Time (ms)')
    ax.set_title(f'All Phases vs κ (N={n})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Top-right: Encryption for different N (dominates)
    ax = axes[0, 1]
    for n in n_values:
        subset = df[df['n'] == n].sort_values('kappa')
        ax.plot(subset['kappa'], subset['enc_ms'], 'o-', label=f'N={n}', lw=2, markersize=5)
    ax.set_xlabel('Dimension (κ)')
    ax.set_ylabel('Encryption Time (ms)')
    ax.set_title('Encryption vs κ (bottleneck)', fontweight='bold')
    ax.legend(title='Users')
    ax.grid(True, alpha=0.3)

    # Bottom-left: Encryption per user (should be independent of N)
    ax = axes[1, 0]
    for n in n_values:
        subset = df[df['n'] == n].sort_values('kappa').copy()
        subset['enc_per_user'] = subset['enc_ms'] / n
        ax.plot(subset['kappa'], subset['enc_per_user'], 'o-', label=f'N={n}', lw=2, markersize=5)
    ax.set_xlabel('Dimension (κ)')
    ax.set_ylabel('Encryption Time per User (ms)')
    ax.set_title('Encryption per User vs κ (parallel!)', fontweight='bold')
    ax.legend(title='Users')
    ax.grid(True, alpha=0.3)

    # Bottom-right: Aggregation per dimension
    ax = axes[1, 1]
    for n in n_values:
        subset = df[df['n'] == n].sort_values('kappa').copy()
        subset['agg_per_dim'] = subset['agg_ms'] / subset['kappa']
        ax.plot(subset['kappa'], subset['agg_per_dim'], 'o-', label=f'N={n}', lw=2, markersize=5)
    ax.set_xlabel('Dimension (κ)')
    ax.set_ylabel('Aggregation Time per Dimension (ms)')
    ax.set_title('Aggregation per Dimension (DLP lookup)', fontweight='bold')
    ax.legend(title='Users')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")

# ============================================================================
# GRAPH 3: Heatmaps
# ============================================================================
def plot_heatmaps(df, output_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    phases = [
        ('setup_ms', 'Setup Time (ms)', axes[0, 0]),
        ('enc_ms', 'Encryption Time (ms)', axes[0, 1]),
        ('agg_ms', 'Aggregation Time (ms)', axes[1, 0]),
        ('verify_ms', 'Verification Time (ms)', axes[1, 1]),
    ]

    for col, title, ax in phases:
        pivot = df.pivot_table(values=col, index='kappa', columns='n', aggfunc='mean')
        sns.heatmap(pivot, ax=ax, annot=True, fmt='.0f', cmap='YlOrRd',
                   cbar_kws={'label': 'ms'})
        ax.set_title(title, fontweight='bold')
        ax.set_xlabel('Number of Users (N)')
        ax.set_ylabel('Dimension (κ)')
        ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")

# ============================================================================
# GRAPH 4: Complexity Analysis
# ============================================================================
def plot_complexity(df, output_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Setup is O(n + kappa)
    ax = axes[0, 0]
    df_copy = df.copy()
    df_copy['n_plus_kappa'] = df_copy['n'] + df_copy['kappa']
    ax.scatter(df_copy['n_plus_kappa'], df_copy['setup_ms'], s=60, color=COLORS['setup'], alpha=0.7)
    z = np.polyfit(df_copy['n_plus_kappa'], df_copy['setup_ms'], 1)
    x_fit = np.linspace(df_copy['n_plus_kappa'].min(), df_copy['n_plus_kappa'].max(), 100)
    ax.plot(x_fit, np.poly1d(z)(x_fit), '--', color='gray', label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
    ax.set_xlabel('N + κ')
    ax.set_ylabel('Setup Time (ms)')
    ax.set_title('Setup Complexity: O(N + κ)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Encryption is O(N * kappa)
    ax = axes[0, 1]
    df_copy['n_times_kappa'] = df_copy['n'] * df_copy['kappa']
    ax.scatter(df_copy['n_times_kappa'], df_copy['enc_ms'], s=60, color=COLORS['encryption'], alpha=0.7)
    z = np.polyfit(df_copy['n_times_kappa'], df_copy['enc_ms'], 1)
    x_fit = np.linspace(df_copy['n_times_kappa'].min(), df_copy['n_times_kappa'].max(), 100)
    ax.plot(x_fit, np.poly1d(z)(x_fit), '--', color='gray', label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
    ax.set_xlabel('N × κ')
    ax.set_ylabel('Encryption Time (ms)')
    ax.set_title('Encryption Complexity: O(N × κ)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Aggregation is O(kappa) with O(1) DLP lookups
    ax = axes[1, 0]
    ax.scatter(df_copy['kappa'], df_copy['agg_ms'], s=60, color=COLORS['aggregation'], alpha=0.7)
    z = np.polyfit(df_copy['kappa'], df_copy['agg_ms'], 1)
    x_fit = np.linspace(df_copy['kappa'].min(), df_copy['kappa'].max(), 100)
    ax.plot(x_fit, np.poly1d(z)(x_fit), '--', color='gray', label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
    ax.set_xlabel('κ')
    ax.set_ylabel('Aggregation Time (ms)')
    ax.set_title('Aggregation Complexity: O(κ) DLP lookups', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Verification is O(n + kappa) pairings
    ax = axes[1, 1]
    ax.scatter(df_copy['n_plus_kappa'], df_copy['verify_ms'], s=60, color=COLORS['verification'], alpha=0.7)
    z = np.polyfit(df_copy['n_plus_kappa'], df_copy['verify_ms'], 1)
    x_fit = np.linspace(df_copy['n_plus_kappa'].min(), df_copy['n_plus_kappa'].max(), 100)
    ax.plot(x_fit, np.poly1d(z)(x_fit), '--', color='gray', label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
    ax.set_xlabel('N + κ')
    ax.set_ylabel('Verification Time (ms)')
    ax.set_title('Verification Complexity: O(N + κ) pairings', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")

# ============================================================================
# GRAPH 5: Scalability Summary
# ============================================================================
def plot_scalability(df, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Time breakdown for different configs
    ax = axes[0]
    configs = [(25, 25), (50, 50), (75, 75), (100, 100)]
    x = range(len(configs))
    width = 0.2

    setup_vals = []
    enc_vals = []
    agg_vals = []
    ver_vals = []

    for n, k in configs:
        row = df[(df['n'] == n) & (df['kappa'] == k)].iloc[0]
        setup_vals.append(row['setup_ms'])
        enc_vals.append(row['enc_ms'])
        agg_vals.append(row['agg_ms'])
        ver_vals.append(row['verify_ms'])

    ax.bar([i - 1.5*width for i in x], setup_vals, width, label='Setup', color=COLORS['setup'])
    ax.bar([i - 0.5*width for i in x], enc_vals, width, label='Encryption', color=COLORS['encryption'])
    ax.bar([i + 0.5*width for i in x], agg_vals, width, label='Aggregation', color=COLORS['aggregation'])
    ax.bar([i + 1.5*width for i in x], ver_vals, width, label='Verification', color=COLORS['verification'])

    ax.set_xlabel('Configuration')
    ax.set_ylabel('Time (ms)')
    ax.set_title('Time Breakdown by Configuration', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'N={n}, κ={k}' for n, k in configs], rotation=15)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Right: Percentage breakdown
    ax = axes[1]
    for i, (n, k) in enumerate(configs):
        row = df[(df['n'] == n) & (df['kappa'] == k)].iloc[0]
        total = row['setup_ms'] + row['enc_ms'] + row['agg_ms'] + row['verify_ms']
        pcts = [
            row['setup_ms'] / total * 100,
            row['enc_ms'] / total * 100,
            row['agg_ms'] / total * 100,
            row['verify_ms'] / total * 100,
        ]

        bottom = 0
        for pct, color, label in zip(pcts,
                                     [COLORS['setup'], COLORS['encryption'], COLORS['aggregation'], COLORS['verification']],
                                     ['Setup', 'Encryption', 'Aggregation', 'Verification']):
            ax.bar(i, pct, bottom=bottom, color=color, label=label if i == 0 else None)
            bottom += pct

    ax.set_xlabel('Configuration')
    ax.set_ylabel('Percentage of Total Time (%)')
    ax.set_title('Time Distribution (Encryption dominates)', fontweight='bold')
    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels([f'N={n}, κ={k}' for n, k in configs], rotation=15)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")

# ============================================================================
# GRAPH 6: Summary Table
# ============================================================================
def create_summary(df, output_path):
    summary_data = []

    for _, row in df.iterrows():
        total = row['setup_ms'] + row['enc_ms'] + row['agg_ms'] + row['verify_ms']
        enc_pct = row['enc_ms'] / total * 100

        summary_data.append({
            'N': int(row['n']),
            'κ': int(row['kappa']),
            'Setup (ms)': f"{row['setup_ms']:.1f}",
            'Enc (ms)': f"{row['enc_ms']:.1f}",
            'Agg (ms)': f"{row['agg_ms']:.1f}",
            'Ver (ms)': f"{row['verify_ms']:.1f}",
            'Total (ms)': f"{total:.1f}",
            'Enc %': f"{enc_pct:.1f}%",
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))

# ============================================================================
# MAIN
# ============================================================================
def main():
    print("="*60)
    print("  Generating Graphs from Existing Benchmark Data")
    print("="*60)

    setup_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    print(f"\nLoaded {len(df)} data points")
    print(f"N values: {sorted(df['n'].unique())}")
    print(f"κ values: {sorted(df['kappa'].unique())}")

    print("\nGenerating graphs...")

    # Generate all graphs
    plot_impact_n(df, OUTPUT_DIR / 'graph_impact_users.png')
    plot_impact_kappa(df, OUTPUT_DIR / 'graph_impact_kappa.png')
    plot_heatmaps(df, OUTPUT_DIR / 'graph_heatmaps.png')
    plot_complexity(df, OUTPUT_DIR / 'graph_scalability.png')
    plot_scalability(df, OUTPUT_DIR / 'graph_breakdown.png')
    create_summary(df, OUTPUT_DIR / 'benchmark_summary.csv')

    print("\n" + "="*60)
    print("  Done!")
    print("="*60)

if __name__ == '__main__':
    main()
