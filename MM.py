import asyncio
import ccxt.pro as ccxtpro
import json

async def stream_data(exchange_id, symbol):
    """
    Streams data from a cryptocurrency exchange using CCXT Pro and WebSockets.

    Args:
        exchange_id (str): The ID of the exchange (e.g., 'binance', 'coinbasepro').
        symbol (str): The trading pair symbol (e.g., 'BTC/USDT', 'ETH/BTC').
    """

    # Check if the exchange is supported by ccxtpro
    if exchange_id not in ccxtpro.exchanges:
        print(f"Exchange '{exchange_id}' not found.")
        return

    # Instantiate the exchange
    exchange_class = getattr(ccxtpro, exchange_id)
    exchange = exchange_class({
        'enableRateLimit': True,  # Optional: Enable rate limiting for exchanges that require it
    })

    # Check if the exchange has fetchOHLCV
    if not exchange.has['watchOHLCV']:
        print(f"'{exchange_id}' does not support 'watchOHLCV'.")
        return

    print(f"Starting to stream data for {symbol} on {exchange_id}...")

    while True:
        try:
            # Watch for OHLCV (candlestick) data
            # candles = await exchange.watch_ohlcv(symbol, '1m')  # 1m timeframe, adjust as needed

            # # Process the received data
            # for candle in candles:
            #     print(f"{exchange_id} {symbol} OHLCV: {candle}")

            # Trades:
            trades = await exchange.watch_trades(symbol)
            for trade in trades:
                print(f"{exchange_id} {symbol} Trade: {trade}")


            # Order book:
            # orderbook = await exchange.watch_order_book(symbol)
            # print(f"{exchange_id} {symbol} Order Book: {orderbook}")

            # Ticker:
            # ticker = await exchange.watch_ticker(symbol)
            # print(f"{exchange_id} {symbol} Ticker: {ticker}")

        except ccxtpro.NetworkError as e:
            print(f"Network error: {e}")
            await asyncio.sleep(exchange.rateLimit / 1000)  # Wait for rate limit
        except ccxtpro.ExchangeError as e:
            print(f"Exchange error: {e}")
            break  # Exit on exchange error
        except Exception as e:
            print(f"Other error: {e}")
            break  # Exit on other errors

    await exchange.close()
    print(f"Finished streaming data for {symbol} on {exchange_id}.")

async def main():
    # Example usage: Stream data from Binance for BTC/USDT
    exchange_id = 'binance'
    symbol = 'BTC/USDT'

    # Example usage: Stream data from Coinbase Pro for ETH/BTC
    # exchange_id = 'coinbasepro'
    # symbol = 'ETH/BTC'
    
    # Example usage: Stream data from multiple exchanges simultaneously
    # await asyncio.gather(
    #     stream_data('binance', 'BTC/USDT'),
    #     stream_data('coinbasepro', 'ETH/BTC'),
    # )
    
    await stream_data(exchange_id, symbol)

if __name__ == '__main__':
    asyncio.run(main())