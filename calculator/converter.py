def toman_to_asset(toman, price):
    if price <= 0:
        return 0

    return toman / price


def asset_to_toman(amount, price):
    if price <= 0:
        return 0

    return amount * price


def format_number(number):
    return f"{number:,.2f}"