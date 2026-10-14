"""Options Atlas API. Demo quotes are synthetic and never represent live markets."""
from __future__ import annotations

import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from analytics import black_scholes, implied_volatility
from providers import DemoProvider

ROOT = Path(__file__).parent
provider = DemoProvider()
app = FastAPI(title="Options Atlas", description="Options intelligence with explicit data provenance.", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])
app.mount("/assets", StaticFiles(directory=ROOT / "static"), name="assets")

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "provider": provider.name, "mode": "demo", "timestamp": provider.timestamp}

@app.get("/api/market")
def market():
    return provider.market()

@app.get("/api/symbols")
def symbols(q: str = Query("", max_length=30)):
    return {"results": provider.search(q)}

@app.get("/api/instruments/{symbol}")
def instrument(symbol: str):
    result = provider.instrument(symbol.upper())
    if result is None:
        raise HTTPException(404, "Symbol not found. Try SPY, QQQ, AAPL, NVDA, or TSLA.")
    return result

@app.get("/api/instruments/{symbol}/chain")
def chain(symbol: str, expiration: Optional[str] = None, side: Optional[str] = None,
          moneyness: str = Query("all", pattern="^(all|itm|atm|otm)$"),
          min_volume: int = Query(0, ge=0, le=10000000), unusual: bool = False,
          limit: int = Query(300, ge=1, le=1000)):
    inst = provider.instrument(symbol.upper())
    if inst is None:
        raise HTTPException(404, "Symbol not found")
    rows = provider.chain(symbol.upper())
    if expiration: rows = [r for r in rows if r["expiration"] == expiration]
    if side in ("call", "put"): rows = [r for r in rows if r["side"] == side]
    if min_volume: rows = [r for r in rows if r["volume"] >= min_volume]
    if unusual: rows = [r for r in rows if r["unusual"]]
    spot = inst["price"]
    if moneyness == "itm": rows = [r for r in rows if r["moneyness"] == "ITM"]
    if moneyness == "otm": rows = [r for r in rows if r["moneyness"] == "OTM"]
    if moneyness == "atm": rows = [r for r in rows if abs(r["strike"] - spot) / spot <= .025]
    return {"symbol": symbol.upper(), "rows": rows[:limit], "count": len(rows), "provenance": provider.provenance}

@app.get("/api/instruments/{symbol}/research")
def research(symbol: str):
    inst = provider.instrument(symbol.upper())
    if inst is None: raise HTTPException(404, "Symbol not found")
    rows = provider.chain(symbol.upper())
    calls = sum(x["volume"] for x in rows if x["side"] == "call")
    puts = sum(x["volume"] for x in rows if x["side"] == "put")
    active = sorted(rows, key=lambda r: r["volume"] / max(r["open_interest"], 1), reverse=True)[:3]
    ivs = [r["iv"] for r in rows]
    return {"symbol": symbol.upper(), "observed": [
        f"{symbol.upper()} is {inst['change_pct']:+.2f}% versus its prior close in this synthetic snapshot.",
        f"Displayed chain volume is {calls:,} calls and {puts:,} puts (put/call volume ratio {puts/max(calls,1):.2f}).",
        f"At-the-money implied volatility is approximately {min(ivs)*100:.1f}%–{max(ivs)*100:.1f}% across the displayed expirations."
    ], "notable_contracts": active, "interpretation": "A higher put/call volume ratio can reflect hedging, directional positioning, or spread activity. Volume alone does not reveal intent. Implied volatility summarizes option prices; it is not a forecast of direction.", "uncertainty": "Synthetic data is generated for product demonstration. No news feed or causal attribution is connected, so this view does not identify why the underlying moved.", "disclaimer": "Research context only; not investment advice.", "provenance": provider.provenance}

@app.get("/api/analytics/greeks")
def greeks(spot: float = Query(..., gt=0), strike: float = Query(..., gt=0), days: float = Query(..., gt=0, le=3650), iv: float = Query(..., gt=0, le=5), rate: float = Query(.04, ge=-.1, le=1), side: str = Query("call", pattern="^(call|put)$")):
    try: return black_scholes(spot, strike, days / 365, iv, rate, side)
    except ValueError as e: raise HTTPException(422, str(e))

@app.get("/api/analytics/implied-volatility")
def iv_endpoint(price: float = Query(..., gt=0), spot: float = Query(..., gt=0), strike: float = Query(..., gt=0), days: float = Query(..., gt=0, le=3650), rate: float = Query(.04, ge=-.1, le=1), side: str = Query("call", pattern="^(call|put)$")):
    try: return {"iv": implied_volatility(price, spot, strike, days / 365, rate, side)}
    except ValueError as e: raise HTTPException(422, str(e))

