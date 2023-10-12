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
    FOREIGN KEY (stock_id) REFERENCES stocks(id)
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


    conn = sqlite3.connect('simple.db')
    db = conn.cursor()
    url = "https://api.zondacrypto.exchange/rest/trading/ticker"
    headers = {'content-type': 'application/json'}
    response = requests.request("GET", url, headers=headers)
    pars= json.loads(response.text)
    dates = pars.get('ticker', {}).get('market', {}).get('items')
    df = pd.DataFrame(pars)
    listt = df.index.tolist()
    ids_zonda = 1
    for item in listt:
        db.execute("INSERT OR IGNORE INTO pairs (stock_id, name) VALUES (?, ?)", (ids_zonda, item,))
    conn.commit()
    conn.close()



    conn = sqlite3.connect('simple.db')
    db = conn.cursor()
    session = HTTP(testnet=True)
    response = session.get_tickers(
                                    category="spot"
    )
    symbols_list = response['result']['list']
    symbol_list = []  # Tworzymy pustą listę na symbole

    for item in symbols_list:
        symbol = item['symbol']
        symbol_list.append(symbol)  # Dodajemy symbol do listy
    ids_bybit = 2
    for item in symbol_list:
        db.execute("INSERT OR IGNORE INTO pairs (stock_id, name) VALUES (?, ?)", (ids_bybit, item,))
    conn.commit()
    conn.close()


    conn = sqlite3.connect('simple.db')
    db = conn.cursor()
    url = f"https://api.binance.com/api/v3/exchangeInfo"
    headers = {'content-type': 'application/json'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    act_price = data.get('symbols')
    ids_binance = 3 
    for item in act_price:
        symbol = item.get('symbol')
        db.execute("INSERT OR IGNORE INTO pairs (stock_id, name) VALUES (?, ?)", (ids_binance, symbol))
    conn.commit()
    conn.close()


    




