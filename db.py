import sqlite3
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
    purch_pairs INTEGER  NOT NULL UNIQUE,
    date DATE NOT NULL,
    count REAL NOT NULL,
    price DECIMAL NOT NULL,
    value DECIMAL NOT NULL,
    FOREIGN KEY (purch_pairs) REFERENCES pairs(id)
    )
    ''')

    # Utwórz tabelę "prices"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
    act_price DECIMAL,
    act_value DECIMAL
    )
    ''')

    # Zapisz zmiany i zamknij połączenie z bazą danych
    conn.commit()
    


# def db_create_main():
#     db = sqlite3.connect("simple.db")
#     cursor = db.cursor()
#     cursor.execute(
#     '''CREATE TABLE IF NOT EXISTS inwestycje(
#             ID	            INTEGER NOT NULL UNIQUE PRIMARY KEY  AUTOINCREMENT,
#             data_zakupu     DATE NOT NULL,
#             gielda          STRING NOT NULL,
#             para            STRING NOT NULL,
#             ilosc           FLOAT NOT NULL,
#             cena_zakupu     FLOAT NOT NULL,
#             wartosc_zakupu  FLOAT NOT NULL,
#             aktualna_cena   FLOAT,
#             aktualna_wartosc Float 
#         );''')

#     db.commit

# def db_create_pairs():
#     db = sqlite3.connect("simple.db")
#     cursor = db.cursor()
#     cursor.execute(
#     '''CREATE TABLE IF NOT EXISTS pairs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             exchange TEXT NOT NULL,
#             pairs TEXT NOT NULL
#         );''')

#     db.commit