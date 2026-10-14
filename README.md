# Options Atlas

Options Atlas is an investor-facing options intelligence MVP. It combines a responsive research dashboard with a Python API for market snapshots, option chains, Black–Scholes analytics, and a cautious activity summary. The interface is designed to make market data legible without treating option activity as a prediction.

## Run locally

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

Run checks with `pytest`.

## Architecture

- `main.py` exposes the FastAPI routes, request validation, static dashboard, and API boundaries.
- `providers.py` contains the data-provider implementation. The `DemoProvider` emits deterministic synthetic examples and a provider timestamp. It is explicitly marked as synthetic in the API and UI.
- `analytics.py` implements European Black–Scholes price/Greeks and bisection implied-volatility solving with range and input checks.
- `static/` is the accessible responsive browser app: searchable tickers, interactive chain filters, chart views, and contextual definitions.

The current provider interface exposes `market()`, `search(query)`, `instrument(symbol)`, and `chain(symbol)`. A vendor adapter can implement the same interface and normalize its authorized feed into these fields. Configure vendor credentials through environment variables (see `.env.example`); do not commit credentials. OPRA access requires an appropriate data-vendor agreement and entitlements. This MVP does not connect to OPRA, scrape market data, or claim that demo prices are live.

## Data and analytics limitations

- The default and only implemented source is synthetic demo data. It is deterministic by symbol, refreshed with a generated timestamp, and is not suitable for trading.
- Demo research summarizes displayed synthetic chain activity. No news feed or event attribution is included; possible causes of price moves are intentionally not fabricated.
- The surface view is a compact term-structure comparison using near-the-money implied volatility. Historical realized volatility is not available in demo mode.
- Greeks and implied volatility use European Black–Scholes assumptions, a continuously compounded constant risk-free rate, and no dividends. Production analytics should account for rates, dividends, exercise style, corporate actions, and vendor conventions.
- The MVP applies bounded request parameters and deterministic in-process demo generation. A production deployment should add authenticated vendor access, shared caching, observability, stronger per-client rate limiting, and market-calendar-aware timestamps.

## API

- `GET /api/health`, `/api/market`, `/api/symbols?q=...`
- `GET /api/instruments/{symbol}`, `/chain`, `/research`
- `GET /api/analytics/greeks` and `/api/analytics/implied-volatility`

All market payloads include provider provenance and timestamps. Validation errors return HTTP 422; unknown symbols return HTTP 404.
