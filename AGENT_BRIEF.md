# OTC Treasury Reconciliation System — Agent Brief

> This document is the single source of truth for building this project.
> Read it fully before executing any task. Do not infer, assume, or add features not listed here.
> If something is ambiguous, stop and ask before proceeding.

---

## Project Overview

This is a **portfolio project** for a Senior Treasury & Finance Operations professional.
It simulates an OTC (Over-The-Counter) crypto/FX reconciliation system used at a licensed
Indonesian fintech, handling USDT/IDR, USDC/IDR, BTC/IDR, and PAXG/IDR transactions.

The project demonstrates:
- Realistic OTC transaction data generation
- Settlement matching logic (buy leg + sell leg)
- PnL recognition on full settlement of both legs
- Discrepancy detection and status tracking
- A live pricer that applies spread + regulatory tax

**Target audience for the final article:** CFOs, Heads of Treasury, Senior Finance Ops
professionals at global fintech and crypto firms. Not data engineers.

---

## Two-Product Structure (CRITICAL — understand this before building anything)

This project produces **two distinct end products** that serve different audiences.
Do not blur them. Do not mix their content or style.

### Product 1: The Writing (delomite.com/blog)

- A long-form article that tells the story of building an OTC reconciliation system
- Written for finance practitioners — no engineering jargon
- Contains embedded Chart.js charts inline with the prose (from `/embeds/`)
- Contains the architecture flow diagram as the hero image
- Does NOT contain raw data, code blocks, or notebook output
- Ends with a clear CTA pointing to Product 2
- Tone: practitioner writing for peers, specific and opinionated

### Product 2: The Project (GitHub repo + hosted tools)

- Full technical documentation for people who want to go deeper
- Contains: Colab notebook, raw CSVs, BI dashboard, pricer API, standalone dashboard
- README references the article — someone landing on GitHub cold should read
  the writing first to understand the context
- Tone: documentation, precise, reproducible

**The two products must point to each other:**
- Article footer → GitHub repo, Colab link, pricer link, BI dashboard link
- GitHub README intro → article link on delomite.com

---

## Repository Structure

```
otc-reconciliation/
│
├── README.md                       <- Public project overview
├── AGENT_BRIEF.md                  <- This document (do not publish)
│
├── data/
│   ├── 01_transactions.csv
│   ├── 02_monthly_pnl.csv
│   ├── 03_account_ledger.csv
│   ├── 04_pricer_template.csv
│   ├── ref_clients.csv
│   ├── ref_market_makers.csv
│   ├── ref_bank_accounts.csv
│   ├── ref_wallets.csv
│   └── ref_exchanges.csv
│
├── notebook/
│   └── otc_reconciliation.ipynb    <- Google Colab notebook
│
├── pricer/
│   ├── main.py                     <- FastAPI app
│   ├── config.py                   <- Editable spread/tax parameters
│   ├── models.py                   <- Pydantic models
│   ├── requirements.txt
│   └── README.md
│
├── embeds/                         <- Chart snippets for delomite.com article
│   ├── chart-01-volume-by-pair.html
│   ├── chart-02-monthly-pnl.html
│   ├── chart-03-waterfall.html
│   ├── chart-04-pnl-donut.html
│   └── chart-05-settlement-status.html
│
├── bi/
│   ├── powerbi.pbix                <- Power BI report file
│   ├── powerbi-screenshots/
│   │   ├── 01-overview.png
│   │   ├── 02-pnl-waterfall.png
│   │   ├── 03-pair-breakdown.png
│   │   └── 04-client-analysis.png
│   └── looker-studio-link.txt      <- Public Looker Studio share URL
│
├── dashboard/
│   └── index.html                  <- Standalone full dashboard (GitHub only)
│
└── diagrams/
    └── architecture_flow.png       <- System flow diagram (hero image)
```

---

## Stage 1: Dataset Generation

### Objective
Generate realistic synthetic OTC transaction data for FY 2024 (Jan 1 to Dec 31).
Minimum 5,000 transactions. Every column must be filled. No nulls. No empty strings.

### Business Rules (CRITICAL - do not deviate)

**Pairs and volume weights:**
| Pair     | Weight | Notes                    |
|----------|--------|--------------------------|
| USDT/IDR | 50%    | Highest frequency stable |
| USDC/IDR | 35%    | Second stablecoin        |
| BTC/IDR  | 10%    | Volatile, wider spread   |
| PAXG/IDR | 5%     | Gold-backed, widest spread |

**Spread ranges (in basis points):**
| Pair     | Min | Max |
|----------|-----|-----|
| USDT/IDR | 12  | 28  |
| USDC/IDR | 15  | 29  |
| BTC/IDR  | 45  | 120 |
| PAXG/IDR | 60  | 150 |

**Regulatory tax:** 0.21% applied on client-facing IDR amount

**Pricing formula:**
- Client BUY quote  = MM rate x (1 + spread_rate + 0.0021)
- Client SELL quote = MM rate x (1 - spread_rate - 0.0021)

**PnL recognition rule:**
- PnL recognized ONLY when BOTH legs are fully settled
- pnl_recognition_timestamp = max(crypto_settled_at, fiat_settled_at)
- pnl_recognition_month = month of pnl_recognition_timestamp
- If status != SETTLED then net_pnl_idr = 0

**Settlement lag by pair:**
| Pair     | Crypto leg   | Fiat leg   |
|----------|-------------|------------|
| USDT/IDR | 0.1-1.0 hrs | 1-4 hrs    |
| USDC/IDR | 0.1-1.0 hrs | 1-4 hrs    |
| BTC/IDR  | 0.5-2.0 hrs | 2-8 hrs    |
| PAXG/IDR | 1.0-4.0 hrs | 4-24 hrs   |

**Transaction status distribution:**
| Status       | Weight |
|--------------|--------|
| SETTLED      | 93%    |
| PENDING      | 3%     |
| RECONCILING  | 3%     |
| FAILED       | 1%     |

**Trading days:** Monday to Friday only. No weekends.

**Daily transaction count:** 18-28 per trading day (~261 trading days in 2024)

**Direction split:** ~55% BUY (client buys crypto), ~45% SELL (client sells crypto)

**Volume ranges (crypto units):**
| Pair     | Min    | Max     |
|----------|--------|---------|
| USDT/IDR | 5,000  | 500,000 |
| USDC/IDR | 5,000  | 400,000 |
| BTC/IDR  | 0.05   | 2.5     |
| PAXG/IDR | 0.5    | 15.0    |

**Base rates - use geometric brownian motion for daily simulation:**
| Pair     | Base Rate (IDR) | Daily Vol std dev |
|----------|----------------|-------------------|
| USDT/IDR | 15,800         | 0.2%              |
| USDC/IDR | 15,800         | 0.2%              |
| BTC/IDR  | 650,000,000    | 3.5%              |
| PAXG/IDR | 30,000,000     | 1.2%              |

---

### Schema: 01_transactions.csv

Every row = one OTC transaction. All fields required.

| Column                      | Type     | Description |
|-----------------------------|----------|-------------|
| transaction_id              | string   | Format: OTC-00001 (zero-padded 5 digits) |
| trade_date                  | date     | YYYY-MM-DD |
| trade_timestamp             | datetime | YYYY-MM-DD HH:MM:SS |
| pair                        | string   | USDT/IDR, USDC/IDR, BTC/IDR, or PAXG/IDR |
| direction                   | string   | BUY or SELL (from client perspective) |
| client_id                   | string   | From ref_clients.csv |
| client_name                 | string   | From ref_clients.csv |
| client_type                 | string   | Corporate / HNWI / Institutional |
| client_tier                 | string   | A / B / C |
| market_maker_id             | string   | From ref_market_makers.csv |
| market_maker_name           | string   | From ref_market_makers.csv |
| volume_crypto               | float    | Crypto units traded |
| mid_price_idr               | float    | Market mid price at time of trade |
| mm_price_idr                | float    | Price quoted by market maker to us |
| client_price_idr            | float    | Price we quote to client |
| spread_bps                  | int      | Our spread in basis points |
| idr_mm_amount               | float    | volume x mm_price (our cost) |
| idr_client_amount           | float    | volume x client_price (client pays/receives) |
| gross_spread_idr            | float    | abs(idr_client_amount - idr_mm_amount) |
| tax_idr                     | float    | idr_client_amount x 0.0021 |
| net_pnl_idr                 | float    | gross_spread - tax_idr (0 if not SETTLED) |
| bank_account_id             | string   | From ref_bank_accounts.csv |
| client_wallet_id            | string   | From ref_wallets.csv |
| mm_wallet_id                | string   | From ref_wallets.csv |
| crypto_settlement_timestamp | datetime | When crypto leg settled |
| fiat_settlement_timestamp   | datetime | When fiat leg settled |
| pnl_recognition_timestamp   | datetime | max(crypto, fiat) settlement time |
| pnl_recognition_month       | string   | YYYY-MM format |
| status                      | string   | SETTLED / PENDING / RECONCILING / FAILED |
| exchange_ref                | string   | From ref_exchanges.csv |
| notes                       | string   | Empty string "" for clean data |

---

### Schema: 02_monthly_pnl.csv

Aggregated from 01_transactions.csv. Settled transactions only.

| Column                 | Description |
|------------------------|-------------|
| pnl_recognition_month  | YYYY-MM |
| pair                   | Trading pair |
| total_transactions     | Count of settled tx |
| total_volume_crypto    | Sum of volume |
| total_idr_client_amount| Sum of client-facing IDR |
| total_gross_spread_idr | Sum of gross spread |
| total_tax_idr          | Sum of tax paid |
| total_net_pnl_idr      | Sum of net PnL |
| avg_spread_bps         | Average spread in bps |

---

### Schema: 03_account_ledger.csv

One row per leg per settled transaction (dual-entry style).

| Column               | Description |
|----------------------|-------------|
| account_id           | Bank or wallet ID |
| account_type         | Bank / Wallet |
| transaction_id       | Links to 01_transactions.csv |
| trade_date           | YYYY-MM-DD |
| pair                 | Trading pair |
| direction            | CREDIT or DEBIT (from account perspective) |
| amount_idr           | IDR equivalent amount |
| settlement_timestamp | When this specific leg settled |
| counterparty         | Client name or MM name |
| status               | Always SETTLED in this table |

---

### Schema: 04_pricer_template.csv

One row per pair. Formula reference only. Not computed data.

| Column                      | Description |
|-----------------------------|-------------|
| pair                        | Trading pair |
| client_volume_crypto        | Placeholder: [INPUT] |
| mm_indicative_rate_idr      | Placeholder: [INPUT] |
| spread_bps                  | Typical range as string |
| spread_rate                 | Formula string |
| tax_rate                    | 0.0021 |
| buy_quote_idr               | Formula string |
| sell_quote_idr              | Formula string |
| idr_total_buy               | Formula string |
| idr_total_sell              | Formula string |
| estimated_gross_spread_idr  | Formula string |
| estimated_tax_idr           | Formula string |
| estimated_net_pnl_idr       | Formula string |
| notes                       | Disclaimer string |

---

### Reference Tables

**ref_clients.csv** - minimum 10 clients
| Column | Values |
|--------|--------|
| id     | CLT-001 through CLT-010 |
| name   | Indonesian corporate/HNWI names |
| type   | Corporate / HNWI / Institutional |
| tier   | A / B / C |

**ref_market_makers.csv** - 3 market makers
| Column | Values |
|--------|--------|
| id     | MM-001, MM-002, MM-003 |
| name   | Generic OTC/liquidity provider names |
| type   | Market Maker |

**ref_bank_accounts.csv** - 4 accounts
| Column   | Values |
|----------|--------|
| id       | BANK-IDR-001, BANK-IDR-002, BANK-IDR-003, BANK-USD-001 |
| bank     | BCA, Mandiri, BNI, DBS Singapore |
| currency | IDR or USD |
| type     | Operating / Settlement / Reserve / Nostro |

**ref_wallets.csv** - 5 wallets
| Column | Values |
|--------|--------|
| id     | WALLET-USDT-001, WALLET-USDT-002, WALLET-USDC-001, WALLET-BTC-001, WALLET-PAXG-001 |
| chain  | TRC20, ERC20, BTC |
| asset  | USDT, USDC, BTC, PAXG |
| type   | Client Settlement / MM Settlement |

**ref_exchanges.csv** - 2 exchanges
| Column   | Values |
|----------|--------|
| id       | EX-001, EX-002 |
| exchange | Binance, Indodax |
| type     | Price Discovery / Hedging |

---

## Stage 2: Flow Diagram

### Objective
System architecture diagram showing the full reconciliation flow.
Hero image for the article. Must be readable for a non-technical finance audience.

### Three layers:

**Layer 1 - Ingestion (dashed border, grey, labeled "Modular / Nice to Have")**
- Bank Statement PDF Parser (pdfplumber)
- On-chain Listener TRC20/ERC20/BTC (tronpy / web3.py / Blockstream API)
- Manual CSV Upload
- All arrows point to: Normalized Transaction Schema
- Footnote: "This project uses synthetic data representing normalized output.
  Parsers are modular and can be added per data source."

**Layer 2 - Reconciliation Engine (solid border, gold #d4a843, main focus)**
- Normalized Transaction Schema
- Matching Logic (buy leg <-> sell leg <-> MM leg)
- Settlement Status Tracker (PENDING -> SETTLED -> RECONCILING -> FAILED)
- PnL Recognition Engine (dual settlement confirmation)
- Discrepancy Flagging

**Layer 3 - Output (solid border, muted blue/green)**
- Monthly PnL Report (CSV)
- Account Ledger (CSV)
- Colab Notebook
- Live Dashboard (HTML)
- BI Reports (Power BI / Looker Studio)
- Pricer API (FastAPI)

---

## Stage 3: Google Colab Notebook

### Objective
Interactive tutorial. Every code cell preceded by a plain-English markdown cell.
Readers click Runtime -> Run All and get every output with zero configuration.

### Data loading (use GitHub raw URLs - no local setup)
```python
BASE_URL = "https://raw.githubusercontent.com/[username]/otc-reconciliation/main/data/"
df = pd.read_csv(BASE_URL + "01_transactions.csv")
```

### Cell structure (in order):

**Cell 1 - Title + Introduction (markdown)**
Project title, author (Gilang Fajar Wijayanto), date.
One paragraph: what problem this solves.
Link to article on delomite.com. Link to architecture diagram.

**Cell 2 - Imports (code)**
pandas, numpy, matplotlib only. Comment every import.

**Cell 3 - Schema Walkthrough (markdown + code)**
Load all CSVs. Print columns and dtypes for 01_transactions.csv.
Explain each key field in plain English.

**Cell 4 - Exploratory Analysis (code + markdown)**
Total transaction count. Count by pair with % breakdown.
Count by status. Monthly transaction count bar chart (matplotlib).

**Cell 5 - Matching Logic (markdown + code)**
Explain two-leg structure. Show how legs pair via transaction_id.
Show dual-entry structure in 03_account_ledger.csv.

**Cell 6 - Settlement Status Engine (markdown + code)**
Explain four statuses. Show status distribution.
Explain difference between RECONCILING and FAILED.

**Cell 7 - PnL Recognition (markdown + code)**
Explain no-warehousing rule. Show pnl_recognition_timestamp logic.
Compare trade_date PnL vs recognition_date PnL (differ at month-end).
Monthly PnL table by pair.

**Cell 8 - Discrepancy Detection (markdown + code)**
Flag: fiat_settlement more than 8 hrs after crypto_settlement.
Flag: RECONCILING status with age more than 24 hrs.
Output a discrepancy report dataframe.

**Cell 9 - Monthly PnL Report (markdown + code)**
Load 02_monthly_pnl.csv. Show gross -> tax -> net by month.
PnL by pair table. Export to CSV.

**Cell 10 - Summary + Next Steps (markdown)**
What this demonstrated. What production adds (parsers, live feeds, alerting).
Links: article, GitHub, pricer API, BI dashboard.

---

## Stage 4: Pricer Web App (FastAPI)

### Objective
Lightweight API that receives a live MM rate and returns a buy/sell quote
with spread and OJK tax applied. Parameters editable without redeployment.

### Endpoints

**POST /quote**
Input:
```json
{
  "pair": "USDT/IDR",
  "mm_rate": 15800.00,
  "volume": 100000,
  "client_tier": "A"
}
```
Output:
```json
{
  "pair": "USDT/IDR",
  "mm_rate": 15800.00,
  "volume": 100000,
  "spread_bps": 20,
  "tax_rate": 0.0021,
  "buy_quote": 15833.32,
  "sell_quote": 15766.92,
  "idr_total_buy": 1583332000,
  "idr_total_sell": 1576692000,
  "gross_spread_idr": 3332000,
  "tax_idr": 3324996,
  "net_pnl_idr": 7004,
  "timestamp": "2024-01-15T10:30:00Z",
  "note": "Indicative only. Confirm before quoting client."
}
```

**GET /params** - returns current spread config for all pairs and tiers
**PUT /params** - updates spread or tax. Requires X-API-Key header.
**GET /health** - returns {"status": "ok", "timestamp": "..."}

### Config (config.py)
```python
PARAMS = {
    "tax_rate": 0.0021,
    "spreads": {
        "USDT/IDR": {"A": 15, "B": 20, "C": 25},
        "USDC/IDR": {"A": 18, "B": 22, "C": 27},
        "BTC/IDR":  {"A": 55, "B": 75, "C": 100},
        "PAXG/IDR": {"A": 70, "B": 95, "C": 130},
    }
}
```

### Stack: FastAPI + Pydantic v2 + Uvicorn. Deploy to Railway or Render free tier.
### Do NOT add: database, Docker, queue systems, auth beyond simple API key.

---

## Stage 5: Chart Embeds for Article (delomite.com)

### Objective
Self-contained Chart.js snippets embedded inline in article prose.
Data baked in as JavaScript objects. No CSV fetch. No external API calls.

### Charts needed
| Chart ID  | Type           | Article section              |
|-----------|----------------|------------------------------|
| chart-01  | Horizontal bar | "Volume by pair"             |
| chart-02  | Line chart     | "Monthly PnL trend"          |
| chart-03  | Grouped bar    | "Gross to Tax to Net"        |
| chart-04  | Donut          | "PnL split by pair"          |
| chart-05  | Horizontal bar | "Settlement rate by status"  |

### Rules
- Each chart = one div wrapper + one script block
- Chart.js CDN: https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js
  (loaded once in blog template, not per chart)
- Width 100% of container
- Heights: horizontal bar=280, line=220, grouped bar=240, donut=260
- No chart titles inside canvas - titles are in the article prose
- responsive: true on all charts

### delomite.com Design System (match exactly - no exceptions)

Colors:
```
Background:   #0a0a0a
Surface:      #111111  <- chart background
Border:       #1e1e1e
Text primary: #f0f0f0
Text muted:   #666666  <- axis labels
Gold:         #d4a843  <- USDT/IDR, primary highlight
Green:        #3ecf8e  <- positive/settled
Red:          #f87171  <- negative/failed
Blue:         #60a5fa  <- USDC/IDR
Orange:       #f7931a  <- BTC/IDR
Purple:       #a78bfa  <- PAXG/IDR
```

Pair color mapping (consistent across ALL charts):
```
USDT/IDR -> #d4a843
USDC/IDR -> #60a5fa
BTC/IDR  -> #f7931a
PAXG/IDR -> #a78bfa
```

Typography: DM Mono monospace. 11px axis labels, 12px tooltips, weight 400.

Chart style:
```
Chart background: #111111
Container border radius: 8px
Grid lines: color #1e1e1e, lineWidth 1
Tooltip: background #1a1a1a, border #2a2a2a, text #f0f0f0
Axis labels: #666666
Bar border radius: 4px
Line tension: 0.4, pointRadius 3, pointHoverRadius 5
Donut cutout: 68%, segment gap 2px
```

Container wrapper (use for every chart):
```html
<div style="background:#111111; border-radius:8px; padding:24px;
            margin:32px 0; font-family:'DM Mono',monospace;">
  <canvas id="chart-XX"></canvas>
</div>
```

Do NOT use: white backgrounds, default Chart.js colors, default tooltip styling,
decorative legend boxes, soft or rounded aesthetics.

---

## Stage 5b: Standalone Dashboard (GitHub only)

File: /dashboard/index.html
Linked from article footer. Not embedded on delomite.com.

Contains:
- All 5 charts combined
- Transaction table with pair filter (All / USDT / USDC / BTC / PAXG)
- Reconciliation view: RECONCILING and FAILED rows with age in hours
- Same design system as Stage 5
- Data baked in as JavaScript objects
- Single self-contained HTML file

---

## Stage 6: BI Reports

### Power BI (build first)

Purpose: reinforces existing Power BI credential on resume.

Visuals required:
- Monthly Net PnL trend (line, by pair)
- Gross to Tax to Net waterfall by month
- Settlement status distribution
- PnL by pair (donut + table)
- Top clients by PnL (horizontal bar)

Slicers: Pair filter, month range slider.

Data source: import 02_monthly_pnl.csv and 01_transactions.csv directly.

Theme: dark background, gold accent, monospace font where available.
Do NOT use default Power BI themes.

Deliverables:
- powerbi.pbix in /bi/
- 4 screenshots in /bi/powerbi-screenshots/
- Short Loom walkthrough 2-3 min - paste link in README

### Looker Studio (build second, optional)

Same visuals as Power BI. Publish with public share link.
Paste URL into /bi/looker-studio-link.txt. No viewer login required.

---

## Stage 7: GitHub Repository

### README.md must contain:
1. One-sentence project description
2. Link to article on delomite.com (first thing after description)
3. Architecture diagram image
4. What this project demonstrates (3-4 bullet points)
5. Folder structure
6. How to run Colab (badge + link)
7. How to run pricer API (3 commands max)
8. All links: Article / Colab / Pricer / Power BI Loom / Looker Studio / Dashboard
9. Author: Gilang Fajar Wijayanto - Senior Treasury & Finance Ops - delomite.com

### Do NOT include:
- AGENT_BRIEF.md contents
- "Synthetic" or "dummy" in the hero section (mention matter-of-factly in Data section)

---

## Stage 8: Article

Written by Gilang. Agents assist with structure and drafts only.

### Structure:
1. Hook - the chaos of manual OTC reconciliation at scale
2. The problem - what breaks settling $300K/day across wallets, banks, and MMs
3. Architecture - flow diagram as hero, explained in plain English
4. The data - schema walkthrough, what each field means and why
   -> embed chart-01 (volume by pair)
5. The build - notebook walkthrough, what each component does
   -> embed chart-05 (settlement status)
6. Results - what the data shows
   -> embed chart-02 (monthly PnL trend)
   -> embed chart-03 (gross to tax to net waterfall)
   -> embed chart-04 (PnL by pair)
7. Lessons - what you would do differently, what production adds
8. Nice to have - parser layer: pdfplumber for bank PDFs,
   tronpy/web3.py for on-chain, Blockstream for BTC. No code, architecture only.
9. Conclusion + links:
   - Full dashboard -> GitHub dashboard link
   - BI reports -> Power BI Loom / Looker Studio link
   - Code + data -> GitHub repo
   - Run in Colab -> Colab link
   - Pricer API -> Railway/Render link

### Tone:
Practitioner writing for peers. Plain English. Specific and opinionated.
No "it depends" without a follow-up answer.

---

## General Rules for Agents

1. Do not add features not listed here. Flag and ask before building anything extra.
2. No nulls, no missing data in any CSV output.
3. Follow the schema exactly. Column names must match character-for-character.
4. Business logic is fixed. Do not change spread ranges, tax rate, or PnL
   recognition rules without explicit instruction.
5. Keep it simple. Portfolio project, not a production system.
   Complexity that does not serve the story is noise.
6. One stage at a time. Complete and verify each stage before starting the next.
7. Output files go in their designated folders per the repository structure above.
8. The two products are separate. Writing = delomite.com. Project = GitHub.
   Do not mix content, style, or audience between them.
9. Charts must match delomite.com design system exactly. No default Chart.js styling.
10. Colab notebook must run with zero local setup. All data from GitHub raw URLs.
