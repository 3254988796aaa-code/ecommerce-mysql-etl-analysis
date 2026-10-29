"""Explicit cleaning rules; source labels are preserved, not inferred."""
from decimal import Decimal, InvalidOperation
import re

FEATURES = ["keyword", "product_name", "repeat_customer_index", "old_shop_index",
            "product_name_length", "location_tag", "product_price", "payment_count", "rating_tag"]


def parse_price(value):
    text = re.sub(r"[¥￥,，\s]", "", str(value))
    try:
        price = Decimal(text)
    except InvalidOperation:
        raise ValueError("invalid_price") from None
    if not price.is_finite() or price <= 0 or price > Decimal("99999999.99"):
        raise ValueError("invalid_price")
    if price != price.quantize(Decimal("0.01")):
        raise ValueError("price_has_subcent_precision")
    return format(price, ".2f")


def parse_payment(value):
    text = re.sub(r"[\s,，]", "", str(value))
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(万|亿)?(\+)?(?:人付款|人已付款|人)?", text)
    if not match:
        raise ValueError("invalid_payment_count")
    amount = Decimal(match[1]) * {None: 1, "万": 10000, "亿": 100000000}[match[2]]
    if amount != amount.to_integral_value() or amount > 9223372036854775807:
        raise ValueError("invalid_payment_count")
    return int(amount), bool(match[3])


def parse_int(value, name, minimum=0, maximum=2147483647):
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"invalid_{name}") from None
    if not number.is_finite() or number != number.to_integral_value() or not minimum <= number <= maximum:
        raise ValueError(f"invalid_{name}")
    return int(number)


def clean_record(raw):
    keyword, name = str(raw.get("keyword") or "").strip(), str(raw.get("product_name") or "").strip()
    if not keyword or not name:
        raise ValueError("missing_required_text")
    if len(keyword) > 100 or len(name) > 512:
        raise ValueError("text_too_long")
    payment, lower_bound = parse_payment(raw.get("payment_raw", ""))
    result = {
        "keyword": keyword, "product_name": name,
        "repeat_customer_index": parse_int(raw.get("repeat_customer_index"), "repeat_customer_index"),
        "old_shop_index": parse_int(raw.get("old_shop_index"), "old_shop_index"),
        "product_name_length": len(name),
        "location_tag": parse_int(raw.get("location_tag"), "location_tag", 1, 5),
        "product_price": parse_price(raw.get("price_raw", "")),
        "payment_count": payment,
        "rating_tag": parse_int(raw.get("rating_tag"), "rating_tag", 0, 1),
        "payment_is_lower_bound": int(lower_bound),
    }
    return result
