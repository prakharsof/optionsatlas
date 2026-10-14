"""Validated Black–Scholes analytics; rates and volatility are decimal annual rates."""
import math

def _cdf(x): return .5 * (1 + math.erf(x / math.sqrt(2)))
def _pdf(x): return math.exp(-.5*x*x) / math.sqrt(2*math.pi)

def black_scholes(spot, strike, t, sigma, rate=.04, side="call"):
    if min(spot, strike, t, sigma) <= 0 or side not in ("call", "put"):
        raise ValueError("spot, strike, time, and volatility must be positive; side must be call or put")
    root = sigma * math.sqrt(t); d1 = (math.log(spot/strike)+(rate+.5*sigma*sigma)*t)/root; d2=d1-root
    discount=math.exp(-rate*t)
    if side == "call": price=spot*_cdf(d1)-strike*discount*_cdf(d2); delta=_cdf(d1)
    else: price=strike*discount*_cdf(-d2)-spot*_cdf(-d1); delta=_cdf(d1)-1
    gamma=_pdf(d1)/(spot*root); vega=spot*_pdf(d1)*math.sqrt(t)/100
    theta_annual=-(spot*_pdf(d1)*sigma)/(2*math.sqrt(t)) + (rate*strike*discount*_cdf(d2) if side=="call" else -rate*strike*discount*_cdf(-d2))
    return {"price": round(price, 6), "delta": round(delta, 6), "gamma": round(gamma, 8), "theta_per_day": round(theta_annual/365, 6), "vega_per_1pct": round(vega, 6)}

def implied_volatility(price, spot, strike, t, rate=.04, side="call"):
    if min(price, spot, strike, t) <= 0 or side not in ("call", "put"):
        raise ValueError("price, spot, strike, and time must be positive; side must be call or put")
    intrinsic=max(spot-strike*math.exp(-rate*t),0) if side=="call" else max(strike*math.exp(-rate*t)-spot,0)
    if price < intrinsic - 1e-8: raise ValueError("option price is below discounted intrinsic value")
    lo, hi=1e-5, 5.0
    if black_scholes(spot,strike,t,hi,rate,side)["price"] < price: raise ValueError("option price exceeds the supported volatility range")
    for _ in range(100):
        mid=(lo+hi)/2
        if black_scholes(spot,strike,t,mid,rate,side)["price"] < price: lo=mid
        else: hi=mid
    return round((lo+hi)/2, 6)
