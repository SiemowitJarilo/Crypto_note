import sqlite3


def db_create_main():
    db = sqlite3.connect("simple.db")
    cursor = db.cursor()
    cursor.execute(
    '''CREATE TABLE IF NOT EXISTS inwestycje(
            ID	            INTEGER NOT NULL UNIQUE PRIMARY KEY  AUTOINCREMENT,
            data_zakupu     DATE NOT NULL,
            gielda          STRING NOT NULL,
            para            STRING NOT NULL,
            ilosc           FLOAT NOT NULL,
            cena_zakupu     FLOAT NOT NULL,
            wartosc_zakupu  FLOAT NOT NULL,
            aktualna_cena   FLOAT 
        );''')

    db.commit

def db_create_pairs():
    db = sqlite3.connect("simple.db")
    cursor = db.cursor()
    cursor.execute(
    '''CREATE TABLE IF NOT EXISTS pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT NOT NULL,
            pairs TEXT NOT NULL
        );''')

    db.commit