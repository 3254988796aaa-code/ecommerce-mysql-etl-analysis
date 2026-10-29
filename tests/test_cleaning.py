from decimal import Decimal
import pytest
from ecommerce.cleaning import parse_price,parse_payment,clean_record


@pytest.mark.parametrize("raw,expected",[("¥1,299.90","1299.90"),("￥ 0.01","0.01"),(169,"169.00")])
def test_prices(raw,expected):
    assert parse_price(raw)==expected


@pytest.mark.parametrize("raw",["free", "-1", "0", "NaN", "Infinity", "1.001"])
def test_invalid_prices(raw):
    with pytest.raises(ValueError):parse_price(raw)


@pytest.mark.parametrize("raw,expected",[("1.2万+人付款",(12000,True)),("800人付款",(800,False)),
    ("1亿+人付款",(100000000,True)),("0人付款",(0,False)),("1,000+人付款",(1000,True))])
def test_payments(raw,expected):
    assert parse_payment(raw)==expected


@pytest.mark.parametrize("raw",["未知","-1人付款","1.5人付款",""])
def test_invalid_payments(raw):
    with pytest.raises(ValueError):parse_payment(raw)


def test_character_count_preserves_symbols_and_digits():
    raw={"keyword":"食品","product_name":"【礼盒】30天","price_raw":"¥10",
         "payment_raw":"100+人付款","repeat_customer_index":0,"old_shop_index":1,"location_tag":1,"rating_tag":0}
    assert clean_record(raw)["product_name_length"]==len(raw["product_name"])
    raw["location_tag"]=9
    with pytest.raises(ValueError,match="invalid_location_tag"):clean_record(raw)
