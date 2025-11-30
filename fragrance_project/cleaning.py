import re
from decimal import Decimal

PRICE_RE = re.compile(r"([0-9\.,]+)")

def parse_price(price_str):
    """
    Return a float price extracted from strings like:
      "$49.99", "AED 150", "149.00"
    Returns None if no number found.
    """
    if not price_str:
        return None
    s = str(price_str).strip()
    # remove thousands separators, keep decimal point
    s_clean = s.replace(",", "")
    m = PRICE_RE.search(s_clean)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        try:
            return float(Decimal(m.group(1)))
        except Exception:
            return None

def normalize_brand(brand):
    if not brand:
        return None
    return str(brand).strip().title()