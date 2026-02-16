from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class QuoteRequest(BaseModel):
    pair: str
    mm_rate: float
    volume: float
    client_tier: str = "A"

class QuoteResponse(BaseModel):
    pair: str
    mm_rate: float
    volume: float
    spread_bps: int
    tax_rate: float
    buy_quote: float
    sell_quote: float
    idr_total_buy: float
    idr_total_sell: float
    gross_spread_idr: float
    tax_idr: float
    net_pnl_idr: float
    timestamp: datetime
    note: str

class ParamsUpdateRequest(BaseModel):
    pair: str
    tier: str
    new_spread_bps: int
