import pandas as pd

# Load data
transactions = pd.read_csv('/Users/gilangfajar/Documents/Personal Files/Project/delomite/satu/data/01_transactions.csv')

# 1. Volume and PnL by Pair
# Assuming 'idr_client_amount' or 'idr_mm_amount' is the volume in IDR.
# Based on the data, 'idr_client_amount' is the total IDR value of the trade for the client.
pair_stats = transactions.groupby('pair').agg(
    total_volume_idr=('idr_client_amount', 'sum'),
    total_net_pnl_idr=('net_pnl_idr', 'sum'),
    avg_spread_bps=('spread_bps', 'mean'),
    tx_count=('transaction_id', 'count')
).reset_index()

# Calculate contribution percentages
total_vol = pair_stats['total_volume_idr'].sum()
total_pnl = pair_stats['total_net_pnl_idr'].sum()

pair_stats['vol_contribution_pct'] = (pair_stats['total_volume_idr'] / total_vol) * 100
pair_stats['pnl_contribution_pct'] = (pair_stats['total_net_pnl_idr'] / total_pnl) * 100

# Rank by volume
pair_stats = pair_stats.sort_values(by='total_volume_idr', ascending=False)

# 2. Market Maker Analysis
# Calculate average spread and total volume provided by each MM, broken down by pair
mm_pair_stats = transactions.groupby(['market_maker_name', 'pair']).agg(
    avg_spread_bps=('spread_bps', 'mean'),
    tx_count=('transaction_id', 'count')
).reset_index()

# Find the best MM for each pair (lowest spread)
print("--- Market Maker 'Generosity' Breakdown by Pair ---")
print(mm_pair_stats.sort_values(['pair', 'avg_spread_bps']).to_string(index=False))

# Quick Summary of Best Routs
print("\n--- Optimal Routing Strategy ---")
for pair in mm_pair_stats['pair'].unique():
    best_mm = mm_pair_stats[mm_pair_stats['pair'] == pair].sort_values('avg_spread_bps').iloc[0]
    print(f"{pair}: Route to {best_mm['market_maker_name']} (Avg Spread: {best_mm['avg_spread_bps']:.2f} bps)")

