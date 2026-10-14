"""Provider interface and deterministic synthetic demo implementation."""
from datetime import datetime, timezone, timedelta
import math, random
from functools import lru_cache

class DemoProvider:
    name = "Synthetic demo provider"
    provenance = {"provider": name, "mode": "synthetic_demo", "is_live": False, "note": "Deterministic illustrative data; not market quotes."}
    def __init__(self):
        self.timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.assets={"SPY":("S&P 500 ETF",586.24,.0042),"QQQ":("Nasdaq 100 ETF",501.88,.0084),"AAPL":("Apple Inc.",236.85,-.0031),"NVDA":("NVIDIA Corp.",178.42,.0128),"TSLA":("Tesla Inc.",441.60,-.0142)}
    def market(self):
        return {"status":"Closed · illustrative snapshot","session":"US equities","timestamp":self.timestamp,"provenance":self.provenance,"indices":[{"symbol":s,"name":n,"price":p,"change_pct":c*100} for s,n,p,c in [("SPY","S&P 500",586.24,.0042),("QQQ","Nasdaq 100",501.88,.0084),("DIA","Dow Jones",428.10,.0017),("IWM","Russell 2000",219.73,-.0036)]]}
    def search(self,q):
        q=q.upper().strip()
        return [{"symbol":s,"name":v[0],"price":v[1]} for s,v in self.assets.items() if not q or q in s or q in v[0].upper()]
    def instrument(self,s):
        if s not in self.assets:return None
        name,price,change=self.assets[s]
        return {"symbol":s,"name":name,"price":price,"change_pct":change*100,"previous_close":round(price/(1+change),2),"timestamp":self.timestamp,"market_status":"Closed · illustrative snapshot","provenance":self.provenance,"expirations":self.expirations()}
    def expirations(self):
        today=datetime.now(timezone.utc).date()
        return [(today+timedelta(days=d)).isoformat() for d in (4,11,25,53,88)]
    @lru_cache(maxsize=32)
    def chain(self,s):
        inst=self.instrument(s)
        if not inst:return []
        spot=inst["price"]; out=[]; rng=random.Random(sum(map(ord,s)))
        for ei,exp in enumerate(self.expirations()):
            days=(datetime.fromisoformat(exp).date()-datetime.now(timezone.utc).date()).days
            for strike in [round(spot*(.85+i*.025),2) for i in range(13)]:
                for side in ("call","put"):
                    iv=.19+.08*abs(strike/spot-1)+.012*ei+(0.035 if side=="put" else 0)
                    g=black_scholes(spot,strike,max(days/365,1/365),iv,.04,side)
                    mid=max(g["price"],.03); spread=max(.02,mid*(.035+rng.random()*.04)); bid=max(.01,mid-spread/2); ask=mid+spread/2
                    oi=rng.randint(80,9000); vol=rng.randint(5,3000)
                    out.append({"expiration":exp,"days_to_expiry":days,"strike":strike,"side":side,"bid":round(bid,2),"ask":round(ask,2),"mid":round((bid+ask)/2,2),"volume":vol,"open_interest":oi,"iv":round(iv,4),"delta":g["delta"],"gamma":g["gamma"],"theta":g["theta_per_day"],"vega":g["vega_per_1pct"],"unusual":vol/max(oi,1)>.75,"moneyness":"ITM" if ((side=="call" and strike<spot) or (side=="put" and strike>spot)) else "OTM"})
        return out

