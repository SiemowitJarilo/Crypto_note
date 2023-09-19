import requests
para = "BTCUSD"
url = f"https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
headers = {'content-type': 'application/json'}

response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()
lowest_ask = data.get('price')
print(type(lowest_ask))
print(data)

    
 