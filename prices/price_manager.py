from api.price_api import get_prices
from database.database_manager import save_price, get_latest_price


def get_all_prices():

    try:

        prices = get_prices()

        for item in prices:

            code = item.get("code")
            value = item.get("value")

            if code and value is not None:
                save_price(code, value)

        return prices

    except Exception as error:

        print("⚠️ API در دسترس نیست:", error)

        old_prices = []

        codes = [
            "USD_RLS",
            "EUR_RLS",
            "GBP_RLS",
            "TRY_RLS",
            "GOLD_18_RLS",
            "BTC_USD"
        ]

        for code in codes:

            old_price = get_latest_price(code)

            if old_price is not None:

                old_prices.append({
                    "code": code,
                    "value": old_price
                })

        return old_prices