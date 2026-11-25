import pytest
from bot.web.order_pricing import installation_quote


@pytest.mark.parametrize("indoor,outdoor,total", [(2, 0, 2550), (2, 2, 4350), (4, 4, 6150), (0, 0, 0), (1, 0, 2050), (0, 1, 2150), (9, 0, 5450)])
def test_shared_rates(indoor, outdoor, total):
    config, amount = installation_quote(dict(indoor=indoor, outdoor=outdoor, nvr=True, mobile=True, price=1))
    assert amount == total
    assert "price" not in config


@pytest.mark.parametrize("value", [None, [], {"indoor": -1}, {"outdoor": 101}, {"indoor": 1.5}, {"indoor": True}, {"indoor": "2"}, {"nvr": "false"}])
def test_invalid_installation(value):
    with pytest.raises(ValueError):
        installation_quote(value)


def test_unspecified_service_packages_are_quote_only():
    from bot.web.site_leads import SERVICE_CATALOG
    assert all(price == 0 for name, price in SERVICE_CATALOG.values())
