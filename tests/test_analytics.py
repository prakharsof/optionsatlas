import pytest
from analytics import black_scholes, implied_volatility

def test_put_call_parity_and_greeks():
    call = black_scholes(100, 100, 1, .2, .04, "call")
    put = black_scholes(100, 100, 1, .2, .04, "put")
    assert call["price"] - put["price"] == pytest.approx(100 - 100 * 2.718281828459045 ** -.04, abs=1e-5)
    assert 0 < call["delta"] < 1 and -1 < put["delta"] < 0
    assert call["gamma"] > 0 and call["vega_per_1pct"] > 0

@pytest.mark.parametrize("side", ["call", "put"])
def test_iv_round_trip(side):
    px = black_scholes(120, 125, .4, .34, .03, side)["price"]
    assert implied_volatility(px, 120, 125, .4, .03, side) == pytest.approx(.34, abs=1e-5)

def test_input_validation():
    with pytest.raises(ValueError): black_scholes(0, 100, .2, .3)
    with pytest.raises(ValueError): implied_volatility(.01, 100, 90, .2, side="call")
