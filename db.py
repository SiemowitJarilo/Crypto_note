import sqlite3, requests, json
import pandas as pd
from pybit.unified_trading import HTTP
def db_create():
    # Utwórz lub połącz się z bazą danych
    conn = sqlite3.connect('simple.db')
    cursor = conn.cursor()

    # Utwórz tabelę "stocks"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    name TEXT UNIQUE NOT NULL
    )
    ''')

    # Utwórz tabelę "pairs"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    stock_id INTEGER  NOT NULL,
    name TEXT NOT NULL,
    base TEXT,
    quote TEXT,
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE (stock_id, name)
    )
    ''')

    # Utwórz tabelę "purchase"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    purch_pairs INTEGER  NOT NULL,
    date DATE NOT NULL,
    count REAL NOT NULL,
    price DECIMAL NOT NULL,
    value DECIMAL NOT NULL,
    currency INTEGER, 
    FOREIGN KEY (purch_pairs) REFERENCES pairs(id)
    )
    ''')

    # Utwórz tabelę "prices"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    act_id INTEGER  NOT NULL UNIQUE,
    act_price DECIMAL,
    act_value DECIMAL,
    FOREIGN KEY (act_id) REFERENCES purchase(id)
    )
    ''')

    # Zapisz zmiany i zamknij połączenie z bazą danych
    conn.commit()

    cursor.execute("INSERT OR IGNORE INTO stocks(name) VALUES ('Zonda'), ('Bybit'), ('Binance'); ")
    conn.commit()


    url = "https://api.zondacrypto.exchange/rest/trading/ticker"
    headers = {'content-type': 'application/json'}
    response = requests.request("GET", url, headers=headers)
    pars= json.loads(response.text)
    pairs = []
    db = sqlite3.connect('simple.db')
    cursor = db.cursor()
    for pair, market_data in pars['items'].items():
        first_currency = market_data['market']['first']['currency']
        second_currency = market_data['market']['second']['currency']
        s_id = 1
        pairs.append({
            'pair': pair,
            'first_currency': first_currency,
            'second_currency': second_currency
        })
        cursor.execute("INSERT OR IGNORE INTO pairs (stock_id, name, base, quote) VALUES (?, ?, ?, ?)", (s_id, pair, first_currency, second_currency))
    db.commit()
 
    url = "https://api.bybit.com/v2/public/symbols"
    response = requests.get(url)
    pairs = []
    s_id = 2
    data = response.json()

    if response.status_code == 200:
        data = response.json()

        for item in data["result"]:
            pair = item["name"]
            first_currency = item["base_currency"]
            second_currency = item["quote_currency"]
            pairs.append({
                'pair': pair,
                'first_currency': first_currency,
                'second_currency': second_currency})
            cursor.execute("INSERT OR IGNORE INTO pairs (stock_id, name, base, quote) VALUES (?, ?, ?, ?)", (s_id, pair, first_currency, second_currency))
        db.commit()


    url = f"https://api.binance.com/api/v3/exchangeInfo"
    headers = {'content-type': 'application/json'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    pairs = []
    s_id = 3 
    if response.status_code == 200:
        data = response.json()
        for item in data["symbols"]:
            pair = item["symbol"]
            first_currency = item["baseAsset"]
            second_currency = item["quoteAsset"]
            pairs.append({
                'pair': pair,
                'first_currency': first_currency,
                'second_currency': second_currency})
            cursor.execute("INSERT OR IGNORE INTO pairs (stock_id, name, base, quote) VALUES (?, ?, ?, ?)", (s_id, pair, first_currency, second_currency))
        db.commit()


    # conn = sqlite3.connect('simple.db')
    # db = conn.cursor()
    # url = f"https://api.binance.com/api/v3/exchangeInfo"
    # headers = {'content-type': 'application/json'}

    # response = requests.get(url, headers=headers)
    # response.raise_for_status()
    # data = response.json()
    # act_price = data.get('symbols')
    # ids_binance = 3 
    # for item in act_price:
    #     symbol = item.get('symbol')
    #     db.execute("INSERT OR IGNORE INTO pairs (stock_id, name) VALUES (?, ?)", (ids_binance, symbol))
    # conn.commit()
    conn.close()


    




