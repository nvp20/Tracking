import asyncio
import ccxt.pro as ccxtpro
import pandas as pd
import numpy as np
import talib
import csv
import os
from datetime import datetime

# --- Configuration ---
exchange_id = 'binance'  # Replace with your preferred exchange
symbol = 'BTC/USDT'     # Replace with your trading pair
timeframe = '1h'        # Timeframe for data
rsi_period = 14
overbought = 80
oversold = 20
hold_bars = 40
simulation_capital = 1000  # Initial capital
csv_filename = 'trading_log.csv'

# --- Column names for the CSV file ---
csv_columns = ['Timestamp', 'Trade #', 'Position Type', 'Entry Price', 'Exit Price', 'Bars Held', 'Profit/Loss', 'Capital', 'In Position', 'Entry Bar', 'Current RSI']

# --- Global Variables ---
in_position = False
position_type = None  # 'long' or 'short'
entry_price = 0
entry_bar = 0
trade_count = 0
current_capital = simulation_capital
current_rsi = 0

async def fetch_ohlcv(exchange, symbol, timeframe, limit=100):
    """Fetches OHLCV data from the exchange."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching OHLCV data: {e}")
        return None

def calculate_rsi(df, period):
    """Calculates the RSI for the given DataFrame."""
    if 'close' in df.columns:
        df['rsi'] = talib.RSI(df['close'], timeperiod=period)
    return df

def load_trading_data():
    """Loads trading data from the CSV file."""
    global in_position, position_type, entry_price, entry_bar, trade_count, current_capital, current_rsi
    
    if os.path.isfile(csv_filename):
        try:
            df = pd.read_csv(csv_filename)
            if not df.empty:
                last_row = df.iloc[-1]
                trade_count = last_row['Trade #']
                current_capital = last_row['Capital']
                in_position = last_row['In Position']
                if in_position:
                    position_type = last_row['Position Type']
                    entry_price = last_row['Entry Price']
                    entry_bar = last_row['Entry Bar']
                current_rsi = last_row['Current RSI']

                print("Loaded trading data from CSV:")
                print(f"  Trade Count: {trade_count}")
                print(f"  Current Capital: {current_capital}")
                print(f"  In Position: {in_position}")
                if in_position:
                    print(f"  Position Type: {position_type}")
                    print(f"  Entry Price: {entry_price}")
                    print(f"  Entry Bar: {entry_bar}")
                print(f"  Current RSI: {current_rsi}")

        except Exception as e:
            print(f"Error loading trading data from CSV: {e}")

def write_to_csv(data):
    """Writes trade data to the CSV file."""
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=csv_columns)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

async def enter_position(bar_index, price, position_type_local, current_rsi):
    """Enters a position (long or short)."""
    global in_position, position_type, entry_price, entry_bar, trade_count, current_capital
    if not in_position:
        in_position = True
        position_type = position_type_local
        entry_price = price
        entry_bar = bar_index
        trade_count += 1
        print(f"{datetime.now()} - {position_type.upper()} {symbol} at {entry_price}, Trade # {trade_count}")
        print(f"  >>> Current Capital: {current_capital}")

        # Log the entry to CSV immediately with current RSI
        timestamp = datetime.now()
        write_to_csv({
            'Timestamp': timestamp,
            'Trade #': trade_count,
            'Position Type': position_type,
            'Entry Price': entry_price,
            'Exit Price': None,  # No exit price yet
            'Bars Held': 0,  # Will be updated on exit
            'Profit/Loss': 0,  # Will be updated on exit
            'Capital': current_capital,
            'In Position': True,
            'Entry Bar': entry_bar,
            'Current RSI': current_rsi
        })

async def exit_position(bar_index, price, df):
    """Exits the current position."""
    global in_position, position_type, entry_price, entry_bar, trade_count, current_capital
    if in_position:
        bars_held = bar_index - entry_bar
        profit_loss = 0

        if position_type == 'long':
            profit_loss = price - entry_price
        elif position_type == 'short':
            profit_loss = entry_price - price

        current_capital += profit_loss
        in_position = False

        print(f"{datetime.now()} - Exit {position_type.upper()} {symbol} at {price}, Profit/Loss: {profit_loss}, Capital: {current_capital}, Trade # {trade_count}")
        print(f"  >>> Bars Held: {bars_held}")

        # Update the last entry in CSV with exit details
        try:
            df_csv = pd.read_csv(csv_filename)
            if not df_csv.empty:
                last_row_index = df_csv.index[-1]
                df_csv.loc[last_row_index, 'Exit Price'] = price
                df_csv.loc[last_row_index, 'Bars Held'] = bars_held
                df_csv.loc[last_row_index, 'Profit/Loss'] = profit_loss
                df_csv.loc[last_row_index, 'Capital'] = current_capital
                df_csv.loc[last_row_index, 'In Position'] = False
                
                df_csv.to_csv(csv_filename, index=False)

        except Exception as e:
            print(f"Error updating exit details in CSV: {e}")

        position_type = None
        entry_price = 0
        entry_bar = 0

async def main():
    """Main function to run the trading strategy."""
    global in_position, position_type, entry_price, entry_bar, trade_count, current_capital, current_rsi

    # --- Load Existing Data ---
    load_trading_data()

    # --- Exchange Initialization ---
    exchange = getattr(ccxtpro, exchange_id)({
        'enableRateLimit': True,
    })

    # --- Load Markets ---
    await exchange.load_markets()

    # --- Initial Data Fetch ---
    df = await fetch_ohlcv(exchange, symbol, timeframe, limit=100)
    if df is None or df.empty:
        print("Could not fetch initial data. Exiting.")
        await exchange.close()
        return
    df = calculate_rsi(df, rsi_period)

    print("Initial data fetched. Starting strategy loop...")

    bar_index = len(df) - 1  # Start from the last fetched bar

    while True:
        try:
            # --- Fetch latest bar ---
            latest_bar_df = await fetch_ohlcv(exchange, symbol, timeframe, limit=2)
            if latest_bar_df is None or latest_bar_df.empty:
                print("Could not fetch latest bar.")
                await asyncio.sleep(exchange.rateLimit / 1000)
                continue

            latest_bar = latest_bar_df.iloc[-1]
            
            # Check if latest is new
            if latest_bar['timestamp'] > df['timestamp'].iloc[-1]:
                # --- Update DataFrame ---
                df = pd.concat([df, latest_bar_df.tail(1)], ignore_index=True)
                df = calculate_rsi(df, rsi_period)
                bar_index += 1

                # --- Trading Logic ---
                current_price = latest_bar['close']
                current_rsi = df['rsi'].iloc[-1]

                print(f"{datetime.now()} - Current Price: {current_price}, RSI: {current_rsi:.2f}")

                # --- Entry Conditions ---
                if not in_position:
                    if current_rsi > overbought:
                        await enter_position(bar_index, current_price, 'long', current_rsi)
                    elif current_rsi < oversold:
                        await enter_position(bar_index, current_price, 'short', current_rsi)

                # --- Exit Conditions ---
                elif in_position:
                    if (bar_index - entry_bar) >= hold_bars:
                        await exit_position(bar_index, current_price, df)
                    else:
                        print(
                            f"  >>> Holding {position_type.upper()} position | Entry: {entry_price} | Bars Held: {bar_index - entry_bar}/{hold_bars} | P/L: {(current_price-entry_price) if position_type == 'long' else (entry_price - current_price):.2f}")

                # Remove old data
                df = df.tail(100)
                bar_index = len(df) - 1

            await asyncio.sleep(exchange.rateLimit / 1000)

        except ccxtpro.NetworkError as e:
            print(f"Network error: {e}")
            await asyncio.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())