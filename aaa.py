from pybit.unified_trading import HTTP

para = "BTCUSDT"
session = HTTP(testnet=True)
response = session.get_tickers(
    category="spot",
    symbol=para)
last_price = response['result']['list'][0]['lastPrice']
if last_price:
        # Sprawdź, czy wartość lowest_ask jest liczbą
        try:
            aktualna_cena = float(last_price)
        except ValueError:
            aktualna_cena = None
print(last_price)