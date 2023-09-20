
import requests
para = "BNBBTC"
url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={para}"
headers = {'content-type': 'application/json'}

response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()
lowest_ask = data.get('price')
lowest_ask = data.get('ticker', {}).get('lowestAsk')
print(lowest_ask)
            #     if lowest_ask:
            #         # Sprawdź, czy wartość lowest_ask jest liczbą
            #         try:
            #             print(lowest_ask)
            #             aktualna_cena = float(lowest_ask)
            #             print(type(lowest_ask))
            #         except ValueError:
            #             aktualna_cena = None
            # except:
            #     pass