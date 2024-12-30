import ccxt.pro

# Set up your Binance API credentials
api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'

# Create an instance of the Binance exchange
exchange = ccxt.pro.binance({
    'apiKey': api_key,
    'apiSecret': api_secret,
    'enableRateLimit': True,
})

# Connect to the WebSocket
exchange.websocket_connect()

exchange.websocket_connect(on_open=my_on_open, on_close=my_on_close, on_error=my_on_error, on_message=my_on_message)
def my_on_open(ws):
    print('WebSocket connection opened')

def my_on_close(ws):
    print('WebSocket connection closed')

def my_on_error(ws, error):
    print('WebSocket error:', error)

def my_on_message(ws, message):
    print('Received message:', message)