from . import config


def compute(pages: int, copies: int, color: bool, duplex: bool) -> int:
    """Total in paise. Server-side only: the client never supplies the amount."""
    per_page = config.PRICE_COLOR_PAISE if color else config.PRICE_BW_PAISE
    total = pages * copies * per_page
    if duplex:
        total = total * (100 - config.DUPLEX_DISCOUNT_PCT) // 100
    return total
