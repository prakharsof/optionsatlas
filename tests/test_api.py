from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_market_and_provider_provenance():
    r=client.get('/api/market'); assert r.status_code==200
    data=r.json(); assert data['provenance']['is_live'] is False and len(data['indices'])==4

def test_search_and_unknown_symbol():
    assert client.get('/api/symbols?q=nv').json()['results'][0]['symbol']=='NVDA'
    assert client.get('/api/instruments/NOPE').status_code==404

def test_chain_filters_and_research():
    all_rows=client.get('/api/instruments/SPY/chain').json()['rows']
    assert all_rows and all_rows[0]['iv']>0
    filtered=client.get('/api/instruments/SPY/chain?side=put&min_volume=1000&unusual=true').json()['rows']
    assert all(r['side']=='put' and r['volume']>=1000 and r['unusual'] for r in filtered)
    assert client.get('/api/instruments/SPY/research').json()['observed']

def test_greeks_endpoint_validation():
    assert client.get('/api/analytics/greeks?spot=100&strike=100&days=30&iv=.3').status_code==200
    assert client.get('/api/analytics/greeks?spot=0&strike=100&days=30&iv=.3').status_code==422
