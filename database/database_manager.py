import sqlite3


def connect_db():
    return sqlite3.connect("prices.db")


def save_price(asset, price):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset TEXT,
            price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute(
        "INSERT INTO prices (asset, price) VALUES (?, ?)",
        (asset, price)
    )

    connection.commit()
    connection.close()


def get_price_one_hour_ago(asset):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT price
        FROM prices
        WHERE asset = ?
        AND created_at <= datetime('now', '-1 hour')
        ORDER BY created_at DESC
        LIMIT 1
    """, (asset,))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None


def get_latest_price(asset):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT price
        FROM prices
        WHERE asset = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (asset,))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None