import ccxt
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint
import time

# Binance API ile bağlantı kurma
exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

# Kointegrasyon ve Pairs Trading stratejisi için parametreler
entry_threshold = 1.5
exit_threshold = 0.5
timeframe = '1d'
min_p_value = 0.05
history_limit = 365

# Varlık listesi
symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT']

# Tarihsel verileri al
def fetch_history(symbol, timeframe, limit):
    since = exchange.parse8601('2020-01-01T00:00:00Z')
    data = exchange.fetch_ohlcv(symbol, timeframe, since, limit=limit)
    return pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']).set_index('timestamp')

# Kointegrasyonlu varlık çiftleri bul
def find_cointegrated_pairs(symbols, timeframe, min_p_value, limit):
    cointegrated_pairs = []
    data = {symbol: fetch_history(symbol, timeframe, limit) for symbol in symbols}

    for i, symbol1 in enumerate(symbols):
        for j, symbol2 in enumerate(symbols[i + 1:]):
            _, p_value, _ = coint(data[symbol1]['close'], data[symbol2]['close'])
            if p_value < min_p_value:
                cointegrated_pairs.append((symbol1, symbol2, p_value))

    return cointegrated_pairs

# Pairs Trading stratejisi
def pairs_trading_strategy(symbol1, symbol2, timeframe, entry_threshold, exit_threshold, limit):
    data1 = fetch_history(symbol1, timeframe, limit)
    data2 = fetch_history(symbol2, timeframe, limit)

    price_ratio = data1['close'] / data2['close']
    mean_ratio = price_ratio.mean()
    std_ratio = price_ratio.std()

    long_entry = mean_ratio - entry_threshold * std_ratio
    long_exit = mean_ratio - exit_threshold * std_ratio
    short_entry = mean_ratio + entry_threshold * std_ratio
    short_exit = mean_ratio + exit_threshold * std_ratio

    current_price1 = data1.iloc[-1]['close']
    current_price2 = data2.iloc[-1]['close']
    current_ratio = current_price1 / current_price2

    if current_ratio < long_entry:
        return 'long'
    elif current_ratio > short_entry:
        return 'short'
    elif long_exit < current_ratio < short_exit:
        return 'exit'
    else:
        return 'hold'

# Sürekli marketi araştırma ve işlem sinyalleri oluşturma
while True:
    cointegrated_pairs = find_cointegrated_pairs(symbols, timeframe, min_p_value, history_limit)
    print(f"Kointegre varlık çiftleri: {cointegrated_pairs}")

    for symbol1, symbol2, p_value in cointegrated_pairs:
        signal = pairs_trading_strategy(symbol1, symbol2, timeframe, entry_threshold, exit_threshold, history_limit)
        print(f"{symbol1} / {symbol2} için işlem sinyali: {signal}")

    print("10 dakika boyunca uyuma geçiliyor.")
    time.sleep(600)  # 10 dakika boyunca uyuma geç (döngüyü duraklat)
