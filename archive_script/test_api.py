import requests
payload = {'date': '2018-11-26 12:00:00', 'keys': 'b_USDCAD'}
r = requests.get('http://0.0.0.0:3030/predict', params=payload)
print(r)
print(r.text)


"5b7127020ba092.73763782"
