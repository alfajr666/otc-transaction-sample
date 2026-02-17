from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from config import PARAMS, API_KEY
from models import QuoteRequest, QuoteResponse, ParamsUpdateRequest

app = FastAPI(title="OTC Pricer API")

# Serve static files (CSS/JS)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now()}

@app.post("/quote", response_model=QuoteResponse)
def get_quote(request: QuoteRequest):
    if request.pair not in PARAMS["spreads"]:
        raise HTTPException(status_code=404, detail="Pair not found")
    
    tier = request.client_tier.upper()
    if tier not in PARAMS["spreads"][request.pair]:
        raise HTTPException(status_code=400, detail="Invalid client tier")
        
    spread_bps = PARAMS["spreads"][request.pair][tier]
    spread_rate = spread_bps / 10000
    tax_rate = PARAMS["tax_rate"]
    
    # Pricing formula
    # Client BUY quote = MM rate × (1 + spread_rate + 0.0021)
    # Client SELL quote = MM rate × (1 − spread_rate − 0.0021)
    
    buy_quote = request.mm_rate * (1 + spread_rate + tax_rate)
    sell_quote = request.mm_rate * (1 - spread_rate - tax_rate)
    
    idr_total_buy = request.volume * buy_quote
    idr_total_sell = request.volume * sell_quote
    
    # Gross spread is the difference between client price and MM price
    # For a Buy: Client pays more than MM rate
    # For a Sell: Client receives less than MM rate
    idr_mm_amount = request.volume * request.mm_rate
    gross_spread_idr = abs(idr_total_buy - idr_mm_amount) if idr_total_buy > idr_mm_amount else abs(idr_total_sell - idr_mm_amount)
    # Corrected logic for response:
    # If it was a BUY request... but since we return both Buy/Sell quotes, 
    # we'll just return the spread based on the provided MM rate.
    # Gross spread per unit = mm_rate * spread_rate
    gross_spread_idr = request.volume * request.mm_rate * spread_rate
    tax_idr = request.volume * request.mm_rate * tax_rate # Simplified tax on MM base for indicative
    # Actually, business rules say tax on client-facing IDR amount.
    # We'll use BUY quote for the spread calculation here as an indicative.
    tax_idr = idr_total_buy * tax_rate
    net_pnl_idr = gross_spread_idr - tax_idr

    return QuoteResponse(
        pair=request.pair,
        mm_rate=request.mm_rate,
        volume=request.volume,
        spread_bps=spread_bps,
        tax_rate=tax_rate,
        buy_quote=round(buy_quote, 2),
        sell_quote=round(sell_quote, 2),
        idr_total_buy=round(idr_total_buy, 0),
        idr_total_sell=round(idr_total_sell, 0),
        gross_spread_idr=round(gross_spread_idr, 0),
        tax_idr=round(tax_idr, 0),
        net_pnl_idr=round(net_pnl_idr, 0),
        timestamp=datetime.now(),
        note="Indicative only. Confirm before quoting client."
    )

@app.get("/params")
def get_params():
    return PARAMS

@app.put("/params")
def update_params(update: ParamsUpdateRequest, x_api_key: str = Depends(verify_api_key)):
    if update.pair not in PARAMS["spreads"]:
        raise HTTPException(status_code=404, detail="Pair not found")
    if update.tier not in PARAMS["spreads"][update.pair]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    PARAMS["spreads"][update.pair][update.tier] = update.new_spread_bps
    return {"status": "updated", "pair": update.pair, "tier": update.tier, "new_spread_bps": update.new_spread_bps}
