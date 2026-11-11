import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

# --- CONFIGURATION ---
# Set the aesthetic style of the plots
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12
})

# 1. LOAD DATA
try:
    df = pd.read_csv('benchmark_results.csv')
    # Clean column names (remove potential leading/trailing spaces)
    df.columns = df.columns.str.strip()
    print("✅ Data loaded successfully!")
    print(f"   Total samples: {len(df)}")
    print("   Columns found:", df.columns.tolist())
except FileNotFoundError:
    print("❌ Error: 'benchmark_results.csv' not found. Run the benchmark runner first.")
    exit()

# Define metrics mapping for cleaner labels
metrics = ['AvgSetup(ms)', 'AvgEnc(ms)', 'AvgAgg(ms)', 'AvgVerify(ms)']
labels_map = {
    'AvgSetup(ms)': 'Setup Phase',
    'AvgEnc(ms)': 'Encryption (User)',
    'AvgAgg(ms)': 'Aggregation (Aggregator)',
    'AvgVerify(ms)': 'Verification (Data Analyzer)'
}

# ==============================================================================
# STATISTICAL ANALYSIS
# ==============================================================================
print("\n" + "="*50)
print("📊 STATISTICAL ANALYSIS")
print("="*50)

# Check complexity: O(1) vs O(N) for Verification
# We fix Kappa to isolate the effect of the number of users
kappa_fixed = df['Kappa'].median() 
subset_n = df[df['Kappa'] == kappa_fixed]

if not subset_n.empty and len(subset_n['NumUsers'].unique()) > 1:
    print(f"\n--- Complexity Analysis (Fixed Kappa={int(kappa_fixed)}) ---")
    
    # We analyze Aggregation and Verification
    for metric in ['AvgAgg(ms)', 'AvgVerify(ms)']:
        # Linear regression: y = slope * x + intercept
        slope, intercept, r_value, p_value, std_err = stats.linregress(subset_n['NumUsers'], subset_n[metric])
        
        # Heuristic to determine complexity class based on slope
        # If slope is very small, it's effectively constant time given the noise
        complexity = "O(N) (Linear)" if slope > 0.005 and r_value > 0.8 else "O(1) (Constant)"
        
        print(f"Metric: {labels_map[metric]}")
        print(f"  > Slope: {slope:.5f} ms/user")
        print(f"  > R-squared: {r_value**2:.4f}")
        print(f"  > Conclusion: Likely {complexity}")
        
        if metric == 'AvgVerify(ms)' and "Linear" in complexity:
            print("  ⚠️ WARNING: Verification appears to be Linear! It should be Constant.")
        if metric == 'AvgVerify(ms)' and "Constant" in complexity:
            print("  ✅ SUCCESS: Verification is Constant Time (as claimed in the paper).")

# ==============================================================================
# PLOTTING FIGURES
# ==============================================================================

# FIGURE 1: Impact of Number of Users (N)
# Focus: Verify the efficiency of the Data Analyzer
kappa_max = df['Kappa'].max()
subset_users = df[df['Kappa'] == kappa_max].sort_values(by='NumUsers')

plt.figure(figsize=(12, 6))
plt.title(f"Performance vs. Number of Users (Fixed Kappa={kappa_max})")

# Plot Aggregation (Should be Linear)
sns.lineplot(data=subset_users, x='NumUsers', y='AvgAgg(ms)', marker='o', label='Aggregation', linewidth=2)
# Plot Verification (Should be Constant)
sns.lineplot(data=subset_users, x='NumUsers', y='AvgVerify(ms)', marker='s', label='Verification', linewidth=3, linestyle='--')

plt.xlabel("Number of Users ($N$)")
plt.ylabel("Time (ms)")
plt.legend()
plt.tight_layout()
plt.savefig('graph_impact_users.png')
print("\n💾 Graph saved: graph_impact_users.png")


# FIGURE 2: Impact of Vector Dimension (Kappa)
# Focus: How the vector size affects operations
users_max = df['NumUsers'].max()
subset_kappa = df[df['NumUsers'] == users_max].sort_values(by='Kappa')

plt.figure(figsize=(12, 6))
plt.title(f"Performance vs. Vector Dimension (Fixed Users={users_max})")

for metric in metrics:
    sns.lineplot(data=subset_kappa, x='Kappa', y=metric, marker='o', label=labels_map[metric])

plt.xlabel("Vector Dimension ($\kappa$)")
plt.ylabel("Time (ms)")
plt.legend()
plt.tight_layout()
plt.savefig('graph_impact_kappa.png')
print("💾 Graph saved: graph_impact_kappa.png")


# FIGURE 3: Heatmaps (2D Overview)
# Useful to see the combined effect of N and Kappa
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle(f"Performance Heatmaps (Time in ms)", fontsize=16)

for i, metric in enumerate(metrics):
    row, col = divmod(i, 2)
    
    # Pivot table: Rows=Kappa, Cols=Users
    pivot_table = df.pivot_table(values=metric, index='Kappa', columns='NumUsers', aggfunc='mean')
    
    sns.heatmap(pivot_table, ax=axes[row, col], annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': 'ms'})
    axes[row, col].set_title(labels_map[metric])
    axes[row, col].invert_yaxis() # Visual preference: low Kappa at the bottom

plt.tight_layout()
plt.savefig('graph_heatmaps.png')
print("💾 Graph saved: graph_heatmaps.png")


# FIGURE 4: Logarithmic Scale Comparison
# To visualize Setup vs Enc vs Agg vs Verify orders of magnitude
plt.figure(figsize=(10, 6))
# Take a slice of data (e.g., max users, min kappa)
subset_log = df[(df['NumUsers'] == df['NumUsers'].max()) & (df['Kappa'] == df['Kappa'].min())]
subset_log_melt = subset_log.melt(
    id_vars=['NumUsers'], 
    value_vars=metrics, 
    var_name='Operation', 
    value_name='Time'
)
# Update labels in the dataframe for the plot
subset_log_melt['Operation'] = subset_log_melt['Operation'].map(labels_map)

sns.barplot(data=subset_log_melt, x='Operation', y='Time', hue='Operation', legend=False)
plt.yscale('log')
plt.title(f"Order of Magnitude Comparison (Log Scale)\n(N={users_max}, $\kappa$={df['Kappa'].min()})")
plt.ylabel("Time (ms) - Log Scale")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig('graph_log_comparison.png')
print("💾 Graph saved: graph_log_comparison.png")

plt.show()