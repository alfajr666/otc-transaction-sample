import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

# Configuration
PROJECT_ROOT = "/Users/gilangfajar/Documents/Personal Files/Project/delomite/satu"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Business Rules
PAIRS = {
    "USDT/IDR": {"weight": 0.50, "spread_bps": (12, 28), "vol": 0.002, "base_rate": 15800, "crypto_min": 5000, "crypto_max": 500000, "crypto_lag": (0.1, 1.0), "fiat_lag": (1, 4)},
    "USDC/IDR": {"weight": 0.35, "spread_bps": (15, 29), "vol": 0.002, "base_rate": 15800, "crypto_min": 5000, "crypto_max": 400000, "crypto_lag": (0.1, 1.0), "fiat_lag": (1, 4)},
    "BTC/IDR":  {"weight": 0.10, "spread_bps": (45, 120), "vol": 0.035, "base_rate": 650000000, "crypto_min": 0.05, "crypto_max": 2.5, "crypto_lag": (0.5, 2.0), "fiat_lag": (2, 8)},
    "PAXG/IDR": {"weight": 0.05, "spread_bps": (60, 150), "vol": 0.012, "base_rate": 30000000, "crypto_min": 0.5, "crypto_max": 15.0, "crypto_lag": (1.0, 4.0), "fiat_lag": (4, 24)},
}

STATUS_WEIGHTS = {"SETTLED": 0.93, "PENDING": 0.03, "RECONCILING": 0.03, "FAILED": 0.01}
TAX_RATE = 0.0021
DIRECTION_WEIGHTS = {"BUY": 0.55, "SELL": 0.45}

# Helper to load reference data
def load_ref(filename):
    return pd.read_csv(os.path.join(DATA_DIR, filename))

clients = load_ref("ref_clients.csv")
mms = load_ref("ref_market_makers.csv")
banks = load_ref("ref_bank_accounts.csv")
wallets = load_ref("ref_wallets.csv")
exchanges = load_ref("ref_exchanges.csv")

# Generate dates for FY 2024 (Trading days only)
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
trading_days = pd.bdate_range(start=start_date, end=end_date)

# Simulate Price Rates (GBM)
daily_rates = {}
for pair, cfg in PAIRS.items():
    n = len(trading_days)
    returns = np.random.normal(0, cfg["vol"], n)
    rates = cfg["base_rate"] * np.exp(np.cumsum(returns))
    daily_rates[pair] = dict(zip(trading_days.date, rates))

# Main transaction data list
transactions = []
tx_id_counter = 1

for day in trading_days:
    num_tx = random.randint(18, 28)
    for _ in range(num_tx):
        pair = random.choices(list(PAIRS.keys()), weights=[c["weight"] for c in PAIRS.values()])[0]
        cfg = PAIRS[pair]
        
        direction = random.choices(list(DIRECTION_WEIGHTS.keys()), weights=list(DIRECTION_WEIGHTS.values()))[0]
        
        # Time of trade
        hour = random.randint(9, 17)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        trade_ts = day.replace(hour=hour, minute=minute, second=second)
        
        # Client & MMR
        client = clients.sample(n=1).iloc[0]
        mm = mms.sample(n=1).iloc[0]
        
        # Volume
        volume = random.uniform(cfg["crypto_min"], cfg["crypto_max"])
        
        # Price
        mid_price = daily_rates[pair][day.date()]
        # MM adds a small deviation from mid
        mm_price = mid_price * (1 + random.uniform(-0.001, 0.001))
        
        # Spread
        spread_bps = random.randint(cfg["spread_bps"][0], cfg["spread_bps"][1])
        spread_rate = spread_bps / 10000
        
        if direction == "BUY":
            # Client pays more: MM + spread + tax
            client_price = mm_price * (1 + spread_rate + TAX_RATE)
        else:
            # Client receives less: MM - spread - tax
            client_price = mm_price * (1 - spread_rate - TAX_RATE)
            
        idr_mm_amount = volume * mm_price
        idr_client_amount = volume * client_price
        gross_spread = abs(idr_client_amount - idr_mm_amount)
        tax_idr = idr_client_amount * TAX_RATE
        
        # Status
        status = random.choices(list(STATUS_WEIGHTS.keys()), weights=list(STATUS_WEIGHTS.values()))[0]
        
        # Settlement Lags
        crypto_lag_hrs = random.uniform(cfg["crypto_lag"][0], cfg["crypto_lag"][1])
        fiat_lag_hrs = random.uniform(cfg["fiat_lag"][0], cfg["fiat_lag"][1])
        
        crypto_settled_at = trade_ts + timedelta(hours=crypto_lag_hrs)
        fiat_settled_at = trade_ts + timedelta(hours=fiat_lag_hrs)
        
        pnl_ts = max(crypto_settled_at, fiat_settled_at)
        pnl_month = pnl_ts.strftime("%Y-%m")
        
        net_pnl = gross_spread - tax_idr if status == "SETTLED" else 0
        
        # Assets
        asset = pair.split("/")[0]
        client_wallet = wallets[wallets["asset"] == asset].iloc[0]["id"]
        mm_wallet = wallets[wallets["type"] == "MM Settlement"].iloc[0]["id"]
        bank_acc = banks[banks["currency"] == "IDR"].sample(n=1).iloc[0]["id"]
        exchange_ref = exchanges.sample(n=1).iloc[0]["id"]

        transactions.append({
            "transaction_id": f"OTC-{tx_id_counter:05d}",
            "trade_date": day.date().isoformat(),
            "trade_timestamp": trade_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "pair": pair,
            "direction": direction,
            "client_id": client["id"],
            "client_name": client["name"],
            "client_type": client["type"],
            "client_tier": client["tier"],
            "market_maker_id": mm["id"],
            "market_maker_name": mm["name"],
            "volume_crypto": volume,
            "mid_price_idr": mid_price,
            "mm_price_idr": mm_price,
            "client_price_idr": client_price,
            "spread_bps": spread_bps,
            "idr_mm_amount": idr_mm_amount,
            "idr_client_amount": idr_client_amount,
            "gross_spread_idr": gross_spread,
            "tax_idr": tax_idr,
            "net_pnl_idr": net_pnl,
            "bank_account_id": bank_acc,
            "client_wallet_id": client_wallet,
            "mm_wallet_id": mm_wallet,
            "crypto_settlement_timestamp": crypto_settled_at.strftime("%Y-%m-%d %H:%M:%S"),
            "fiat_settlement_timestamp": fiat_settled_at.strftime("%Y-%m-%d %H:%M:%S"),
            "pnl_recognition_timestamp": pnl_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "pnl_recognition_month": pnl_month,
            "status": status,
            "exchange_ref": exchange_ref,
            "notes": ""
        })
        tx_id_counter += 1

df_tx = pd.DataFrame(transactions)
df_tx.to_csv(os.path.join(DATA_DIR, "01_transactions.csv"), index=False)

# 02_monthly_pnl.csv
settled_df = df_tx[df_tx["status"] == "SETTLED"]
monthly_pnl = settled_df.groupby(["pnl_recognition_month", "pair"]).agg(
    total_transactions=("transaction_id", "count"),
    total_volume_crypto=("volume_crypto", "sum"),
    total_idr_client_amount=("idr_client_amount", "sum"),
    total_gross_spread_idr=("gross_spread_idr", "sum"),
    total_tax_idr=("tax_idr", "sum"),
    total_net_pnl_idr=("net_pnl_idr", "sum"),
    avg_spread_bps=("spread_bps", "mean")
).reset_index()
monthly_pnl.to_csv(os.path.join(DATA_DIR, "02_monthly_pnl.csv"), index=False)

# 03_account_ledger.csv (Dual Entry style)
ledger = []
for idx, row in settled_df.iterrows():
    # Crypto Leg
    ledger.append({
        "account_id": row["client_wallet_id"],
        "account_type": "Wallet",
        "transaction_id": row["transaction_id"],
        "trade_date": row["trade_date"],
        "pair": row["pair"],
        "direction": "CREDIT" if row["direction"] == "BUY" else "DEBIT",
        "amount_idr": row["idr_client_amount"], # For simplification, we track IDR equivalent in ledger
        "settlement_timestamp": row["crypto_settlement_timestamp"],
        "counterparty": row["market_maker_name"],
        "status": "SETTLED"
    })
    # Fiat Leg
    ledger.append({
        "account_id": row["bank_account_id"],
        "account_type": "Bank",
        "transaction_id": row["transaction_id"],
        "trade_date": row["trade_date"],
        "pair": row["pair"],
        "direction": "DEBIT" if row["direction"] == "BUY" else "CREDIT",
        "amount_idr": row["idr_client_amount"],
        "settlement_timestamp": row["fiat_settlement_timestamp"],
        "counterparty": row["client_name"],
        "status": "SETTLED"
    })

pd.DataFrame(ledger).to_csv(os.path.join(DATA_DIR, "03_account_ledger.csv"), index=False)

print(f"Generated {len(df_tx)} transactions.")
