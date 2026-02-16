import pandas as pd
import json
import os
import re

# Paths
PROJECT_ROOT = "/Users/gilangfajar/Documents/Personal Files/Project/delomite/satu"
DASHBOARD_PATH = os.path.join(PROJECT_ROOT, "dashboard/index.html")
TX_PATH = os.path.join(PROJECT_ROOT, "data/01_transactions.csv")

def optimize():
    print("🚀 Optimizing dashboard data payload (Premium Design)...")
    
    # 1. Load Data
    df = pd.read_csv(TX_PATH)
    df['trade_timestamp'] = pd.to_datetime(df['trade_timestamp'])
    df['trade_date'] = df['trade_timestamp'].dt.date
    df = df.sort_values('trade_timestamp', ascending=False)
    
    # Calculate overall stats
    total_count = len(df)
    settled_count = len(df[df['status'] == 'SETTLED'])
    pending_count = len(df[df['status'] == 'PENDING'])
    recon_count = len(df[df['status'] == 'RECONCILING'])
    failed_count = len(df[df['status'] == 'FAILED'])
    settlement_rate = (settled_count / total_count * 100) if total_count > 0 else 0
    
    # Filter settled transactions for aggregation
    settled_df = df[df['status'] == 'SETTLED'].copy()
    
    # Calculate financial metrics
    total_volume = settled_df['idr_client_amount'].sum()
    net_pnl = settled_df['net_pnl_idr'].sum()
    gross_spread = settled_df['gross_spread_idr'].sum()
    total_tax = settled_df['tax_idr'].sum()
    avg_spread = settled_df['spread_bps'].mean()
    
    # 2. Monthly Aggregation
    settled_df['month'] = settled_df['trade_timestamp'].dt.strftime('%b')
    monthly_grouped = settled_df.groupby('month').agg({
        'net_pnl_idr': 'sum',
        'gross_spread_idr': 'sum',
        'tax_idr': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = []
    for m in month_order:
        row = monthly_grouped[monthly_grouped['month'] == m]
        if not row.empty:
            monthly_data.append({
                "m": m,
                "pnl": int(row['net_pnl_idr'].values[0]),
                "gross": int(row['gross_spread_idr'].values[0]),
                "tax": int(row['tax_idr'].values[0]),
                "tx": int(row['transaction_id'].values[0])
            })
        else:
            monthly_data.append({"m": m, "pnl": 0, "gross": 0, "tax": 0, "tx": 0})
    
    # 3. Pair Data
    pair_grouped = settled_df.groupby('pair').agg({
        'net_pnl_idr': 'sum',
        'transaction_id': 'count',
        'spread_bps': 'mean'
    }).reset_index()
    
    pair_colors = {
        "USDT/IDR": "#26a17b",
        "USDC/IDR": "#2775ca",
        "BTC/IDR": "#f7931a",
        "PAXG/IDR": "#d4a843"
    }
    
    pair_cls = {
        "USDT/IDR": "usdt",
        "USDC/IDR": "usdc",
        "BTC/IDR": "btc",
        "PAXG/IDR": "paxg"
    }
    
    pair_data = []
    for _, row in pair_grouped.iterrows():
        pair_data.append({
            "pair": row['pair'],
            "pnl": int(row['net_pnl_idr']),
            "tx": int(row['transaction_id']),
            "bps": round(row['spread_bps'], 1),
            "color": pair_colors.get(row['pair'], "#6b7280"),
            "cls": pair_cls.get(row['pair'], "default")
        })
    
    # Sort by PnL descending
    pair_data = sorted(pair_data, key=lambda x: x['pnl'], reverse=True)
    
    # 4. Client PnL (Top 8)
    client_grouped = settled_df.groupby('client_name')['net_pnl_idr'].sum().reset_index()
    client_grouped = client_grouped.sort_values('net_pnl_idr', ascending=False).head(8)
    
    client_pnl = []
    for _, row in client_grouped.iterrows():
        client_pnl.append({
            "name": row['client_name'],
            "pnl": int(row['net_pnl_idr'])
        })
    
    # 5. Recent Transactions (Latest 20 settled)
    recent_tx = settled_df.head(20)[['transaction_id', 'trade_date', 'pair', 'direction', 'client_name', 
                                      'volume_crypto', 'client_price_idr', 'idr_client_amount', 
                                      'spread_bps', 'net_pnl_idr', 'status']].copy()
    
    recent_tx_data = []
    for _, row in recent_tx.iterrows():
        recent_tx_data.append({
            "id": row['transaction_id'],
            "date": str(row['trade_date']),
            "pair": row['pair'],
            "dir": row['direction'],
            "client": row['client_name'],
            "vol": int(row['volume_crypto']),
            "rate": int(row['client_price_idr']),
            "amt": int(row['idr_client_amount']),
            "bps": int(row['spread_bps']),
            "pnl": int(row['net_pnl_idr']),
            "status": row['status']
        })
    
    # 6. Build JavaScript
    js_monthly = "const monthly = " + json.dumps(monthly_data, indent=2) + ";"
    js_pair = "const pairData = " + json.dumps(pair_data, indent=2) + ";"
    js_client = "const clientPnl = " + json.dumps(client_pnl, indent=2) + ";"
    js_recent = "const recentTx = " + json.dumps(recent_tx_data, indent=2) + ";"
    
    # 7. Inject into HTML
    with open(DASHBOARD_PATH, 'r') as f:
        content = f.read()
    
    # Replace data section
    pattern = r'// BAKED DATA.*?// STATE-MARKER'
    replacement = f'''// BAKED DATA
{js_monthly}

{js_pair}

{js_client}

{js_recent}

// STATE-MARKER'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    
    # 8. Update hardcoded KPI values in HTML using simple replacements
    # We'll use a more direct approach to avoid regex backreference issues
    
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Net PnL (first occurrence)
        if '<div class="kpi-value gold">IDR' in line and 'B</div>' in line:
            line = f'          <div class="kpi-value gold">IDR {net_pnl/1e9:.1f}B</div>'
        
        # Total Volume
        elif '<div class="kpi-value green">IDR' in line and 'T</div>' in line:
            line = f'          <div class="kpi-value green">IDR {total_volume/1e12:.1f}T</div>'
        
        # Total Transactions count (ALL transactions, not just settled)
        elif '<div class="kpi-value blue">' in line and '</div>' in line and 'kpi-label">Total Transactions' in '\n'.join(new_lines[-5:]):
            line = f'          <div class="kpi-value blue">{total_count:,}</div>'
        
        # Settlement rate
        elif '% settlement rate</div>' in line:
            line = f'          <div class="kpi-sub">{settlement_rate:.1f}% settlement rate</div>'
        
        # Average spread
        elif '<div class="kpi-value purple">' in line and 'bps</div>' in line:
            line = f'          <div class="kpi-value purple">{int(avg_spread)} bps</div>'
        
        # Status pills
        elif '<div class="num">' in line and '</div>' in line:
            if 'status-pill settled' in '\n'.join(new_lines[-3:]):
                line = f'          <div class="num">{settled_count:,}</div>'
            elif 'status-pill pending' in '\n'.join(new_lines[-3:]):
                line = f'          <div class="num">{pending_count:,}</div>'
            elif 'status-pill recon' in '\n'.join(new_lines[-3:]):
                line = f'          <div class="num">{recon_count:,}</div>'
            elif 'status-pill failed' in '\n'.join(new_lines[-3:]):
                line = f'          <div class="num">{failed_count:,}</div>'
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open(DASHBOARD_PATH, 'w') as f:
        f.write(content)
        
    size_kb = os.path.getsize(DASHBOARD_PATH) / 1024
    print(f"✅ Dashboard optimized. New size: {size_kb:.2f} KB")
    print(f"📊 Stats: {settled_count:,} settled / {total_count:,} total transactions")
    print(f"💰 Net PnL: IDR {net_pnl/1e9:.1f}B | Volume: IDR {total_volume/1e12:.1f}T")

if __name__ == "__main__":
    optimize()
