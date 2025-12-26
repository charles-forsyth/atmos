from atmos.utils import get_stargazing_conditions

def test_stargazing_logic():
    # Clear sky
    res = get_stargazing_conditions(10, "WAXING_CRESCENT")
    assert "Excellent" in res
    
    # Cloudy
    res = get_stargazing_conditions(90, "NEW_MOON")
    assert "Poor" in res
    
    # Full moon downgrade
    res = get_stargazing_conditions(10, "FULL_MOON")
    assert "Good" in res # Downgraded from Excellent
    assert "Bright Moon" in res
    
    # Seasonality check (simple existence)
    assert "Look for:" in res
