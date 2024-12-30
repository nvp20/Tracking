import ccxt



# Initialize exchange

exchange = ccxt.binance()



# Get funding rate for BTC/USDT market

funding_rate = exchange.fetch_funding_rate('BTC/USDT')



print(f"Funding Rate for BTC/USDT: {funding_rate['fundingRate']}")
