import threading
import numpy as np
import CONFIG
from binance.client import Client
import json
import pprint
import talib
import datetime
import math

client = Client(CONFIG.api_key, CONFIG.api_secret)
closes = []
highs = []
lows = []
PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADING_SYMBOL = 'ETHUSD'
TRADE_QTY = 1.5

in_position = False


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


def logger(text):
    print(text)
    now_IR = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now_GMT = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    with open('logs.txt', 'a') as log:
        log.write(
            '##### {} (IR) - {} (GMT) #####\n{}\n\n'.format(now_IR, now_GMT, text))
        log.close()


def trade_history(purchase_type, date, close, qty, total, rsi, k, d):
    text = '{} !\nAt: {}\nPirce: {}\nQTY: {}\nTotal: ${}\nInfo: RSI = {} , Stock_k = {}, Stock_d = {}\n################################\n\n'.format(
        purchase_type, date, close, qty, total, rsi, k, d)
    with open('{}.txt'.format(datetime.datetime.now().strftime("%Y-%m-%d")), "a") as f:
        f.write(text)
        f.close()


def create_order(purchase_type):
    global in_position

    result = client.create_test_order(
        TRADING_SYMBOL, purchase_type, Client.ORDER_TYPE_LIMIT, TRADE_QTY)

    if purchase_type == 'SELL':
        in_position = False

    in_position = True

    return result


def RSI(closes):
    rsi = talib.RSI(closes, PERIOD)

    last_rsi = rsi[-1]

    return last_rsi


def STOCH(highs, lows, closes):
    stock_k, stock_d = talib.STOCH(highs, lows, closes, PERIOD)

    last_stoch_k = stock_k[-1]
    last_stoch_d = stock_d[-1]

    return last_stoch_k, last_stoch_d


def calculate_data(np_highs, np_lows, np_closes):
    last_rsi = RSI(np_closes)
    last_stoch_k, last_stoch_d = STOCH(np_highs, np_lows, np_closes)

    return last_rsi, last_stoch_k, last_stoch_d


def main():

    global in_position

    klines = client.get_historical_klines(
        "ETHUSDT", Client.KLINE_INTERVAL_1MINUTE, "30 min ago UTC")

    time_GMT = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    for line in klines:
        highs.append(float(line[2]))
        lows.append(float(line[3]))
        closes.append(float(line[4]))

    np_highs = numpy.array(highs)
    np_lows = numpy.array(lows)
    np_closes = numpy.array(closes)

    last_rsi, last_stoch_k, last_stoch_d = calculate_data(
        np_highs, np_lows, np_closes)

    close = float(closes[-1])
    total = TRADE_QTY * close

    # logger('''Close: {}\nLast RSI: {}\nLast Stochastic: k:{}, d:{}\n'''.format(
    #     close, last_rsi, last_stoch_k, last_stoch_d))

    print('''Close: {}\nLast RSI: {}\nLast Stochastic: k:{}, d:{}\n'''.format(
        close, last_rsi, last_stoch_k, last_stoch_d))

    if last_rsi <= RSI_OVERSOLD and math.isnan(last_stoch_k) == False and last_stoch_k <= 20 and last_stoch_d <= 20:
        if in_position:
            logger("Already have some no need!")
        else:
            trade_history(
                'BUY',
                time_GMT,
                close,
                TRADE_QTY,
                total + (total * 0.001),
                last_rsi,
                last_stoch_k,
                last_stoch_d
            )
            in_position = True
            logger('Buy Buy Buy!')
            # logger(create_order('BUY'))

    if last_rsi >= RSI_OVERBOUGHT and math.isnan(last_stoch_k) == False and last_stoch_k >= 80 and last_stoch_d >= 80:

        if in_position:
            trade_history(
                'SELL',
                time_GMT,
                close,
                TRADE_QTY,
                total - (total * 0.001),
                last_rsi,
                last_stoch_k,
                last_stoch_d
            )
            in_position = False
            logger('Sell Sell Sell!')
        else:
            logger('Nothing to sell!')


main()
set_interval(main, 2)
