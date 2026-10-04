import time

from prices.price_manager import get_all_prices
from database.database_manager import get_price_one_hour_ago
from calculator.converter import toman_to_asset, asset_to_toman
from bale.bale_bot import get_updates, send_message, answer_callback_query
from alerts.alert_manager import check_alert


print("ربات در حال اجراست...")

offset = None

prices_cache = []
last_update = 0

user_state = {}
button_mode = {}

alerts = {}


def make_keyboard(rows):
    return {
        "keyboard": [[{"text": x} for x in row] for row in rows],
        "resize_keyboard": True
    }


def make_inline(rows):
    return {
        "inline_keyboard": [
            [{"text": x, "callback_data": x} for x in row]
            for row in rows
        ]
    }


def get_menu(mode="keyboard"):
    rows = [
        ["💵 دلار", "💶 یورو"],
        ["🇬🇧 پوند", "🇹🇷 لیر"],
        ["🥇 طلا", "₿ بیت‌کوین"],
        ["🧮 تبدیل ارز", "🔔 هشدار قیمت"],
        ["🔄 شروع مجدد"]
    ]
    return make_inline(rows) if mode == "glass" else make_keyboard(rows)


def get_button_type_menu():
    return make_keyboard([["🪟 دکمه شیشه‌ای", "⌨️ دکمه کیبوردی"]])


def get_style_menu(mode="keyboard"):
    rows = [["👔 رسمی", "😎 دوستانه"]]
    return make_inline(rows) if mode == "glass" else make_keyboard(rows)


def get_convert_menu(mode="keyboard"):
    rows = [
        ["💵 دلار", "💶 یورو"],
        ["🇬🇧 پوند", "🇹🇷 لیر"],
        ["🥇 طلا", "₿ بیت‌کوین"],
        ["❌ لغو"]
    ]
    return make_inline(rows) if mode == "glass" else make_keyboard(rows)


def get_alert_menu(mode="keyboard"):
    rows = [
        ["💵 دلار", "💶 یورو"],
        ["🇬🇧 پوند", "🇹🇷 لیر"],
        ["🥇 طلا", "₿ بیت‌کوین"],
        ["❌ لغو"]
    ]
    return make_inline(rows) if mode == "glass" else make_keyboard(rows)


def get_direction_menu(mode="keyboard"):
    rows = [
        ["💰 تومان ← ارز", "💵 ارز ← تومان"],
        ["❌ لغو"]
    ]
    return make_inline(rows) if mode == "glass" else make_keyboard(rows)


def get_cancel_menu(mode="keyboard"):
    return make_inline([["❌ لغو"]]) if mode == "glass" else make_keyboard([["❌ لغو"]])


def update_prices():

    global prices_cache
    global last_update

    try:

        prices_cache = get_all_prices()
        last_update = time.time()

        print("قیمت‌ها به‌روزرسانی شدند.")

    except Exception as error:

        print("خطا در دریافت قیمت‌ها:", error)


def get_price(code):

    for item in prices_cache:

        if item.get("code") == code:
            return item.get("value")

    return None


def format_price(code, price, style):

    if price is None:
        return "❌ قیمت پیدا نشد."

    names = {
        "USD_RLS": "💵 دلار",
        "EUR_RLS": "💶 یورو",
        "GBP_RLS": "🇬🇧 پوند",
        "TRY_RLS": "🇹🇷 لیر",
        "GOLD_18_RLS": "🥇 طلای ۱۸ عیار",
        "BTC_USD": "₿ بیت‌کوین"
    }

    name = names.get(code, "قیمت")

    if code == "BTC_USD":
        current_price = price
    else:
        current_price = price / 10

    old_price = get_price_one_hour_ago(code)

    if style == "friendly":
        text = f"😎 {name}\n\n"
    else:
        text = f"{name}\n\n"

    if code == "BTC_USD":
        text += f"💰 قیمت فعلی: ${current_price:,.2f}"
    else:
        text += f"💰 قیمت فعلی: {current_price:,.0f} تومان"

    if old_price is not None:

        if code == "BTC_USD":
            old_price_display = old_price
        else:
            old_price_display = old_price / 10

        change = current_price - old_price_display

        if old_price_display != 0:
            percent = (change / old_price_display) * 100
        else:
            percent = 0

        if change > 0:
            icon = "📈"
        elif change < 0:
            icon = "📉"
        else:
            icon = "➖"

        text += "\n\n"
        text += "🕐 قیمت یک ساعت قبل: "

        if code == "BTC_USD":
            text += f"${old_price_display:,.2f}"
        else:
            text += f"{old_price_display:,.0f} تومان"

        text += "\n"
        text += f"{icon} تغییر: "

        if code == "BTC_USD":
            text += f"${change:,.2f}"
        else:
            text += f"{change:,.0f} تومان"

        text += f"\n📊 درصد تغییر: {percent:+.2f}%"

        if style == "friendly":

            if change > 0:
                text += "\n\n🔥 قیمت رفته بالا! حواست به تغییرات باشه رفیق 😎"

            elif change < 0:
                text += "\n\n👀 یه کم اومده پایین؛ تغییرات بعدی رو هم زیر نظر داشته باش."

            else:
                text += "\n\n😎 فعلاً تغییر خاصی نداشته، رفیق!"

    else:

        text += "\n\n🕐 اطلاعات یک ساعت قبل هنوز موجود نیست."

        if style == "friendly":
            text += "\n\n😎 به محض اینکه اطلاعات کافی داشته باشیم، تغییرات رو هم بهت می‌گیم!"

    return text


def get_conversion_price(code):

    price = get_price(code)

    if price is None:
        return None

    if code == "BTC_USD":
        return None

    return price / 10


def check_alerts():

    if not alerts:
        return

    finished_alerts = []

    for chat_id, alert in alerts.items():

        code = alert["code"]
        target = alert["target"]

        current_price = get_price(code)

        if current_price is None:
            continue

        if code == "BTC_USD":
            display_price = current_price
            unit = "دلار"
        else:
            display_price = current_price / 10
            unit = "تومان"

        if check_alert(display_price, target):

            send_message(
                chat_id,
                f"🔔 هشدار قیمت!\n\n"
                f"قیمت موردنظر به هدف رسید یا از آن عبور کرد.\n\n"
                f"💰 قیمت فعلی: {display_price:,.2f} {unit}\n"
                f"🎯 قیمت هدف: {target:,.2f} {unit}",
                get_menu(button_mode.get(chat_id, "keyboard"))
            )

            finished_alerts.append(chat_id)

    for chat_id in finished_alerts:
        del alerts[chat_id]


update_prices()


while True:

    try:

        if time.time() - last_update >= 30:
            update_prices()
            check_alerts()

        updates = get_updates(offset)

        for update in updates.get("result", []):

            offset = update["update_id"] + 1

            callback = update.get("callback_query")

            if callback:
                callback_id = callback.get("id")
                data = callback.get("data", "")
                callback_message = callback.get("message", {})
                chat = callback_message.get("chat", {})
                chat_id = chat.get("id")
                text = data

                if callback_id:
                    try:
                        answer_callback_query(callback_id)
                    except Exception as error:
                        print("خطا در پاسخ به دکمه شیشه‌ای:", error)

            else:
                message = update.get("message")
                if not message:
                    continue
                chat_id = message["chat"]["id"]
                text = message.get("text", "")

            if text == "/start":

                user_state[chat_id] = {
                    "step": "choose_button",
                    "button_mode": button_mode.get(chat_id, "keyboard")
                }

                send_message(
                    chat_id,
                    "سلام 👋\n\n"
                    "لطفاً نوع دکمه‌ها را انتخاب کن:",
                    get_button_type_menu()
                )

            elif text in ("🪟 دکمه شیشه‌ای", "⌨️ دکمه کیبوردی"):

                button_mode[chat_id] = "glass" if text == "🪟 دکمه شیشه‌ای" else "keyboard"
                user_state[chat_id] = {
                    "step": "choose_style",
                    "button_mode": button_mode[chat_id]
                }

                send_message(
                    chat_id,
                    "نوع دکمه انتخاب شد. ✅\n\n"
                    "لطفاً نوع پاسخ ربات را انتخاب کن:",
                    get_style_menu(button_mode[chat_id])
                )

            elif text == "👔 رسمی":

                user_state[chat_id] = {
                    "step": "main",
                    "style": "formal",
                    "button_mode": button_mode.get(chat_id, "keyboard")
                }

                send_message(
                    chat_id,
                    "حالت رسمی فعال شد. 👔",
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "😎 دوستانه":

                user_state[chat_id] = {
                    "step": "main",
                    "style": "friendly",
                    "button_mode": button_mode.get(chat_id, "keyboard")
                }

                send_message(
                    chat_id,
                    "حالت دوستانه فعال شد 😎🔥",
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "🔄 شروع مجدد":

                user_state[chat_id] = {
                    "step": "choose_button"
                }

                send_message(
                    chat_id,
                    "سلام 👋\n\n"
                    "لطفاً نوع دکمه‌ها را انتخاب کن:",
                    get_button_type_menu()
                )

            elif text == "🔔 هشدار قیمت":

                style = user_state.get(chat_id, {}).get("style", "formal")

                user_state[chat_id] = {
                    "step": "choose_alert_asset",
                    "style": style
                }

                send_message(
                    chat_id,
                    "🔔 هشدار قیمت\n\n"
                    "برای کدوم مورد می‌خوای هشدار تنظیم کنی؟",
                    get_alert_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif chat_id in user_state and user_state[chat_id]["step"] == "choose_alert_asset":

                alert_assets = {
                    "💵 دلار": "USD_RLS",
                    "💶 یورو": "EUR_RLS",
                    "🇬🇧 پوند": "GBP_RLS",
                    "🇹🇷 لیر": "TRY_RLS",
                    "🥇 طلا": "GOLD_18_RLS",
                    "₿ بیت‌کوین": "BTC_USD"
                }

                if text in alert_assets:

                    code = alert_assets[text]

                    style = user_state[chat_id]["style"]

                    user_state[chat_id] = {
                        "step": "enter_alert_price",
                        "code": code,
                        "style": style
                    }

                    names = {
                        "USD_RLS": "دلار",
                        "EUR_RLS": "یورو",
                        "GBP_RLS": "پوند",
                        "TRY_RLS": "لیر",
                        "GOLD_18_RLS": "طلای ۱۸ عیار",
                        "BTC_USD": "بیت‌کوین"
                    }

                    if code == "BTC_USD":

                        send_message(
                            chat_id,
                            f"🔔 هشدار {names[code]}\n\n"
                            "قیمت هدف را به دلار وارد کن.\n\n"
                            "مثلاً:\n"
                            "100000"
                        )

                    else:

                        send_message(
                            chat_id,
                            f"🔔 هشدار {names[code]}\n\n"
                            "قیمت هدف را به تومان وارد کن.\n\n"
                            "مثلاً:\n"
                            "300000"
                        )

            elif chat_id in user_state and user_state[chat_id]["step"] == "enter_alert_price":

                try:

                    target_price = float(
                        text.replace(",", "")
                        .replace("٬", "")
                        .replace("،", "")
                        .strip()
                    )

                    if target_price <= 0:
                        raise ValueError

                    code = user_state[chat_id]["code"]
                    style = user_state[chat_id]["style"]

                    alerts[chat_id] = {
                        "code": code,
                        "target": target_price
                    }

                    user_state[chat_id] = {
                        "step": "main",
                        "style": style
                    }

                    if code == "BTC_USD":
                        unit = "دلار"
                    else:
                        unit = "تومان"

                    send_message(
                        chat_id,
                        f"✅ هشدار ثبت شد!\n\n"
                        f"🎯 قیمت هدف: {target_price:,.0f} {unit}\n\n"
                        "وقتی قیمت به این مقدار یا بیشتر برسد، بهت خبر می‌دم.",
                        get_menu(button_mode.get(chat_id, "keyboard"))
                    )

                except ValueError:

                    send_message(
                        chat_id,
                        "❌ لطفاً فقط یک عدد معتبر وارد کن.\n\n"
                        "مثلاً:\n"
                        "300000"
                    )

            elif text == "🧮 تبدیل ارز":

                style = user_state.get(chat_id, {}).get("style", "formal")

                user_state[chat_id] = {
                    "step": "choose_asset",
                    "style": style
                }

                send_message(
                    chat_id,
                    "🧮 تبدیل ارز\n\n"
                    "اول انتخاب کن می‌خوای با کدوم ارز کار کنی:",
                    get_convert_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "❌ لغو":

                style = user_state.get(chat_id, {}).get("style", "formal")

                user_state[chat_id] = {
                    "step": "main",
                    "style": style
                }

                send_message(
                    chat_id,
                    "❌ عملیات لغو شد.",
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif chat_id in user_state and user_state[chat_id]["step"] == "choose_asset":

                asset_codes = {
                    "💵 دلار": "USD_RLS",
                    "💶 یورو": "EUR_RLS",
                    "🇬🇧 پوند": "GBP_RLS",
                    "🇹🇷 لیر": "TRY_RLS",
                    "🥇 طلا": "GOLD_18_RLS",
                    "₿ بیت‌کوین": "BTC_USD"
                }

                if text in asset_codes:

                    code = asset_codes[text]
                    style = user_state[chat_id]["style"]

                    if code == "BTC_USD":

                        send_message(
                            chat_id,
                            "₿ تبدیل بیت‌کوین فعلاً در این مرحله پشتیبانی نمی‌شود.\n"
                            "بعداً تبدیل بیت‌کوین رو هم اضافه می‌کنیم.",
                            get_menu(button_mode.get(chat_id, "keyboard"))
                        )

                        user_state[chat_id] = {
                            "step": "main",
                            "style": style
                        }

                    else:

                        user_state[chat_id] = {
                            "step": "choose_direction",
                            "code": code,
                            "style": style
                        }

                        send_message(
                            chat_id,
                            "حالا نوع تبدیل رو انتخاب کن:",
                            get_direction_menu(button_mode.get(chat_id, "keyboard"))
                        )

            elif chat_id in user_state and user_state[chat_id]["step"] == "choose_direction":

                if text == "💰 تومان ← ارز":

                    user_state[chat_id]["step"] = "enter_amount"
                    user_state[chat_id]["direction"] = "toman_to_asset"

                    send_message(
                        chat_id,
                        "💰 مبلغ تومان را وارد کن.\n\n"
                        "مثلاً:\n"
                        "100000000",
                        {
                            "keyboard": [
                                [{"text": "❌ لغو"}]
                            ],
                            "resize_keyboard": True
                        }
                    )

                elif text == "💵 ارز ← تومان":

                    user_state[chat_id]["step"] = "enter_amount"
                    user_state[chat_id]["direction"] = "asset_to_toman"

                    send_message(
                        chat_id,
                        "💰 مقدار ارز را وارد کن.\n\n"
                        "مثلاً:\n"
                        "500",
                        {
                            "keyboard": [
                                [{"text": "❌ لغو"}]
                            ],
                            "resize_keyboard": True
                        }
                    )

            elif chat_id in user_state and user_state[chat_id]["step"] == "enter_amount":

                try:

                    amount = float(
                        text.replace(",", "")
                        .replace("٬", "")
                        .strip()
                    )

                    code = user_state[chat_id]["code"]
                    direction = user_state[chat_id]["direction"]
                    style = user_state[chat_id]["style"]

                    price = get_conversion_price(code)

                    if price is None:

                        send_message(
                            chat_id,
                            "❌ قیمت این مورد در دسترس نیست.",
                            get_menu(button_mode.get(chat_id, "keyboard"))
                        )

                    else:

                        names = {
                            "USD_RLS": "دلار",
                            "EUR_RLS": "یورو",
                            "GBP_RLS": "پوند",
                            "TRY_RLS": "لیر",
                            "GOLD_18_RLS": "گرم طلای ۱۸ عیار"
                        }

                        name = names[code]

                        if direction == "toman_to_asset":

                            result = toman_to_asset(amount, price)

                            send_message(
                                chat_id,
                                f"🧮 نتیجه تبدیل\n\n"
                                f"💰 مبلغ: {amount:,.0f} تومان\n"
                                f"📌 قیمت هر واحد: {price:,.0f} تومان\n\n"
                                f"✅ می‌توانی حدوداً:\n"
                                f"{result:,.4f} {name}\n"
                                f"خریداری کنی.",
                                get_menu(button_mode.get(chat_id, "keyboard"))
                            )

                        else:

                            result = asset_to_toman(amount, price)

                            send_message(
                                chat_id,
                                f"🧮 نتیجه تبدیل\n\n"
                                f"💰 مقدار: {amount:,.0f} {name}\n"
                                f"📌 قیمت هر واحد: {price:,.0f} تومان\n\n"
                                f"🇮🇷 ارزش تقریبی:\n"
                                f"{result:,.0f} تومان",
                                get_menu(button_mode.get(chat_id, "keyboard"))
                            )

                    user_state[chat_id] = {
                        "step": "main",
                        "style": style
                    }

                except ValueError:

                    send_message(
                        chat_id,
                        "❌ مقدار واردشده درست نیست.\n\n"
                        "فقط عدد وارد کن.\n"
                        "مثلاً:\n"
                        "500"
                    )

            elif text == "💵 دلار":

                style = user_state.get(chat_id, {}).get("style", "formal")
                price = get_price("USD_RLS")

                send_message(
                    chat_id,
                    format_price("USD_RLS", price, style),
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "💶 یورو":

                style = user_state.get(chat_id, {}).get("style", "formal")
                price = get_price("EUR_RLS")

                send_message(
                    chat_id,
                    format_price("EUR_RLS", price, style),
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "🇬🇧 پوند":

                style = user_state.get(chat_id, {}).get("style", "formal")
                price = get_price("GBP_RLS")

                send_message(
                    chat_id,
                    format_price("GBP_RLS", price, style),
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "🇹🇷 لیر":

                style = user_state.get(chat_id, {}).get("style", "formal")
                price = get_price("TRY_RLS")

                send_message(
                    chat_id,
                    format_price("TRY_RLS", price, style),
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "🥇 طلا":

                style = user_state.get(chat_id, {}).get("style", "formal")
                price = get_price("GOLD_18_RLS")

                send_message(
                    chat_id,
                    format_price("GOLD_18_RLS", price, style),
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

            elif text == "₿ بیت‌کوین":

                style = user_state.get(chat_id, {}).get("style", "formal")
                price = get_price("BTC_USD")

                send_message(
                    chat_id,
                    format_price("BTC_USD", price, style),
                    get_menu(button_mode.get(chat_id, "keyboard"))
                )

        time.sleep(0.2)

    except Exception as error:

        print("خطا:", error)

        time.sleep(2)