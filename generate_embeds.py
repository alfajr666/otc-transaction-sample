import pandas as pd
import json
import os

PROJECT_ROOT = "/Users/gilangfajar/Documents/Personal Files/Project/delomite/satu"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EMBED_DIR = os.path.join(PROJECT_ROOT, "embeds")

# Load data
df_tx = pd.read_csv(os.path.join(DATA_DIR, "01_transactions.csv"))
df_pnl = pd.read_csv(os.path.join(DATA_DIR, "02_monthly_pnl.csv"))

# Design System constants
COLORS = {
    "USDT/IDR": "#d4a843",
    "USDC/IDR": "#60a5fa",
    "BTC/IDR": "#f7931a",
    "PAXG/IDR": "#a78bfa",
    "background": "#0a0a0a",
    "surface": "#111111",
    "border": "#1e1e1e",
    "text": "#f0f0f0",
    "muted": "#666666",
    "green": "#3ecf8e",
    "red": "#f87171"
}

FONT = "'DM Mono', monospace"

def generate_html_wrapper(canvas_id, height, script_content):
    return f"""<div style="background:{COLORS['surface']}; border-radius:8px; padding:24px; margin:32px 0; font-family:{FONT}; color:{COLORS['text']};">
  <canvas id="{canvas_id}" height="{height}"></canvas>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <script>
  (function() {{
    {script_content}
  }})();
  </script>
</div>"""

# ---------------------------------------------------------
# Chart 01: Volume by Pair (Horizontal Bar)
# ---------------------------------------------------------
vol_data = df_pnl.groupby("pair")["total_volume_crypto"].sum().to_dict()
# For display, we'll simplify the volume labels
chart_01_script = f"""
    const ctx = document.getElementById('chart-01').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {list(vol_data.keys())},
            datasets: [{{
                data: {list(vol_data.values())},
                backgroundColor: {list([COLORS[p] for p in vol_data.keys()])},
                borderRadius: 4
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor: '#1a1a1a', titleFont: {{ family: {json.dumps(FONT)} }}, bodyFont: {{ family: {json.dumps(FONT)} }} }} }},
            scales: {{
                x: {{ grid: {{ color: '{COLORS['border']}' }}, ticks: {{ color: '{COLORS['muted']}', font: {{ family: {json.dumps(FONT)}, size: 10 }} }} }},
                y: {{ grid: {{ display: false }}, ticks: {{ color: '{COLORS['text']}', font: {{ family: {json.dumps(FONT)}, size: 11 }} }} }}
            }}
        }}
    }});
"""
with open(os.path.join(EMBED_DIR, "chart-01-volume-by-pair.html"), "w") as f:
    f.write(generate_html_wrapper("chart-01", 280, chart_01_script))

# ---------------------------------------------------------
# Chart 02: Monthly PnL Trend (Line)
# ---------------------------------------------------------
pnl_trend = df_pnl.groupby("pnl_recognition_month")["total_net_pnl_idr"].sum().to_dict()
chart_02_script = f"""
    const ctx = document.getElementById('chart-02').getContext('2d');
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {list(pnl_trend.keys())},
            datasets: [{{
                data: {list(pnl_trend.values())},
                borderColor: '{COLORS['USDT/IDR']}',
                backgroundColor: 'rgba(212, 168, 67, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor: '#1a1a1a' }} }},
            scales: {{
                x: {{ grid: {{ color: '{COLORS['border']}' }}, ticks: {{ color: '{COLORS['muted']}', font: {{ family: {json.dumps(FONT)}, size: 10 }} }} }},
                y: {{ grid: {{ color: '{COLORS['border']}' }}, ticks: {{ color: '{COLORS['muted']}', font: {{ family: {json.dumps(FONT)}, size: 10 }} }} }}
            }}
        }}
    }});
"""
with open(os.path.join(EMBED_DIR, "chart-02-monthly-pnl.html"), "w") as f:
    f.write(generate_html_wrapper("chart-02", 220, chart_02_script))

# ---------------------------------------------------------
# Chart 03: Gross -> Tax -> Net (Grouped Bar)
# ---------------------------------------------------------
waterfall = df_pnl.sum()
labels = ["Gross Spread", "Tax Paid", "Net PnL"]
values = [waterfall["total_gross_spread_idr"], waterfall["total_tax_idr"], waterfall["total_net_pnl_idr"]]
chart_03_script = f"""
    const ctx = document.getElementById('chart-03').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {labels},
            datasets: [{{
                data: {values},
                backgroundColor: ['{COLORS['accent_purple'] if 'accent_purple' in COLORS else '#a78bfa'}', '{COLORS['red']}', '{COLORS['green']}'],
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                x: {{ grid: {{ display: false }}, ticks: {{ color: '{COLORS['text']}', font: {{ family: {json.dumps(FONT)}, size: 11 }} }} }},
                y: {{ grid: {{ color: '{COLORS['border']}' }}, ticks: {{ color: '{COLORS['muted']}', font: {{ family: {json.dumps(FONT)}, size: 10 }} }} }}
            }}
        }}
    }});
"""
with open(os.path.join(EMBED_DIR, "chart-03-waterfall.html"), "w") as f:
    f.write(generate_html_wrapper("chart-03", 240, chart_03_script))

# ---------------------------------------------------------
# Chart 04: PnL Split (Donut)
# ---------------------------------------------------------
pnl_split = df_pnl.groupby("pair")["total_net_pnl_idr"].sum().to_dict()
chart_04_script = f"""
    const ctx = document.getElementById('chart-04').getContext('2d');
    new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: {list(pnl_split.keys())},
            datasets: [{{
                data: {list(pnl_split.values())},
                backgroundColor: {list([COLORS[p] for p in pnl_split.keys()])},
                borderWidth: 2,
                borderColor: '{COLORS['surface']}'
            }}]
        }},
        options: {{
            cutout: '68%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ 
                legend: {{ 
                    position: 'right', 
                    labels: {{ color: '{COLORS['text']}', font: {{ family: {json.dumps(FONT)}, size: 11 }}, boxWidth: 12 }} 
                }} 
            }}
        }}
    }});
"""
with open(os.path.join(EMBED_DIR, "chart-04-pnl-donut.html"), "w") as f:
    f.write(generate_html_wrapper("chart-04", 260, chart_04_script))

# ---------------------------------------------------------
# Chart 05: Settlement Status (Horizontal Bar)
# ---------------------------------------------------------
status_data = df_tx["status"].value_counts().to_dict()
chart_05_script = f"""
    const ctx = document.getElementById('chart-05').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {list(status_data.keys())},
            datasets: [{{
                data: {list(status_data.values())},
                backgroundColor: ['{COLORS['green']}', '{COLORS['USDT/IDR']}', '{COLORS['BTC/IDR']}', '{COLORS['red']}'],
                borderRadius: 4
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                x: {{ grid: {{ color: '{COLORS['border']}' }}, ticks: {{ color: '{COLORS['muted']}', font: {{ family: {json.dumps(FONT)}, size: 10 }} }} }},
                y: {{ grid: {{ display: false }}, ticks: {{ color: '{COLORS['text']}', font: {{ family: {json.dumps(FONT)}, size: 11 }} }} }}
            }}
        }}
    }});
"""
with open(os.path.join(EMBED_DIR, "chart-05-settlement-status.html"), "w") as f:
    f.write(generate_html_wrapper("chart-05", 280, chart_05_script))

print(f"Generated 5 embeds in {EMBED_DIR}")
