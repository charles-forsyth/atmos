from atmos.wardrobe import WardrobeAdviser


def test_wardrobe_freezing():
    advice = WardrobeAdviser.advise(
        temp_f=20.0,
        feels_like_f=10.0,
        precip_prob=0.0,
        precip_rate=0.0,
        uv_index=1,
        wind_speed=15.0,
        humidity=40.0,
        desc="Clear",
    )
    assert "Heavy thermal base layers (wool or synthetic)" in advice["clothing"]
    assert (
        "Heavy insulated winter parka (windproof & waterproof)" in advice["outerwear"]
    )
    assert "Heavy insulated snow boots with good traction" in advice["footwear"]
    assert (
        "Significant wind chill! It feels 10.0°F colder than actual. Add an extra wind-blocking layer."
        in advice["warnings"]
    )


def test_wardrobe_rainy():
    advice = WardrobeAdviser.advise(
        temp_f=55.0,
        feels_like_f=55.0,
        precip_prob=80.0,
        precip_rate=0.1,
        uv_index=1,
        wind_speed=8.0,
        humidity=90.0,
        desc="Light Rain",
    )
    assert "Waterproof rain jacket, rain shell, or poncho" in advice["outerwear"]
    assert "Compact, windproof umbrella" in advice["gear"]
    assert "Water-resistant boots or treated waterproof sneakers" in advice["footwear"]


def test_wardrobe_hot_sunny():
    advice = WardrobeAdviser.advise(
        temp_f=85.0,
        feels_like_f=92.0,
        precip_prob=0.0,
        precip_rate=0.0,
        uv_index=7,
        wind_speed=5.0,
        humidity=75.0,
        desc="Sunny",
    )
    assert (
        "Loose, light-colored, and highly breathable fabrics (linen/cotton)"
        in advice["clothing"]
    )
    assert "Broad-spectrum sunscreen (SPF 30+)" in advice["gear"]
    assert "UV-protective sunglasses" in advice["gear"]
    assert "Wide-brimmed sun hat or baseball cap" in advice["gear"]
    assert (
        "Very high UV index. Reapply sunscreen every 2 hours and seek shade between 10 AM and 4 PM."
        in advice["warnings"]
    )
    assert (
        "High heat index! It feels 7.0°F warmer and muggier than actual. Hydrate often and limit heavy exertion."
        in advice["warnings"]
    )


def test_wardrobe_mild():
    advice = WardrobeAdviser.advise(
        temp_f=65.0,
        feels_like_f=65.0,
        precip_prob=10.0,
        precip_rate=0.0,
        uv_index=2,
        wind_speed=5.0,
        humidity=45.0,
        desc="Partly Cloudy",
    )
    assert "Standard t-shirt, polo, or light long-sleeve shirt" in advice["clothing"]
    assert "Light sweater, cardigan, or zip-up hoodie" in advice["clothing"]
    assert (
        "Light jacket, denim jacket, windbreaker, or bomber jacket"
        in advice["outerwear"]
    )
