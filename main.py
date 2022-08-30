import time
import pandas as pd
import requests
import json
import os
import configparser
from bitbank import Bitbank

start_balance = 100000 #運用開始時の日本円残高
jpy_balance = start_balance #日本円
btc_balance = 0 #btc数量
amount = 0.001 #一回あたりの取引数量
fee = 0.12*0.01 #取引手数料(率）

conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['bitbank']['access_key']
SECRET_KEY = conf['bitbank']['secret_key']

# print(ACCESS_KEY)
# print(SECRET_KEY)

bitbank = Bitbank(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

ticker = 'btc'
pair = ticker + '_jpy'
interval = 60*1 #移動平均をとる時間足、5分足
duration = 2

df = pd.DataFrame()

def trade(current_price, side):
    global jpy_balance
    global btc_balance
    global amount
    if side == 'buy':
        jpy_balance -= (current_price * amount + current_price * amount * fee)
        btc_balance += amount
    elif side == 'sell':
        jpy_balance += (current_price * amount - current_price * amount * fee)
        btc_balance -= amount
    elif side == 'through':
        pass
    else:
        pass

    total_balance = jpy_balance + btc_balance * current_price
    df['side'] = side
    df['JPY'] = jpy_balance
    df['BTC'] = btc_balance
    df['Total'] = total_balance
    df['P&L'] = total_balance - start_balance 
    print(jpy_balance)
    print(btc_balance)
    print(total_balance)
    print(side)

while True:
    time.sleep(interval)
    position = bitbank.position

    if not position.get('jpy'):
        raise

    df = df.append({'price': bitbank.last(pair)}, ignore_index=True)

    if len(df) < duration:
        print(len(df))
        print('now collecting data...')
        continue

    print(len(df))

    df['SMA'] = df['price'].rolling(window=duration).mean()
    df['std'] = df['price'].rolling(window=duration).std()
    df['-2sigma'] = df['SMA'] - 0.1*df['std']
    df['+2sigma'] = df['SMA'] + 0.1*df['std']
    # df['-2sigma'] = df['SMA'] - 2*df['std']
    # df['+2sigma'] = df['SMA'] + 2*df['std']

    # 取引の判断
    if ticker in position.keys():
        if float(df['price'].iloc[-1]) > df['+2sigma'].iloc[-1] and btc_balance > 0:
            # and bitbank.check_ex_rate(pair) < float(df['price'].iloc[-1])
                trade(float(df['price'].iloc[-1]), 'sell')          
        else:
            if float(df['price'].iloc[-1]) < df['-2sigma'].iloc[-1]:
                trade(float(df['price'].iloc[-1]), 'buy')
            else:
                trade(float(df['price'].iloc[-1]), 'through')

    # データファイルを出力する
    path = 'data.csv'
    is_file = os.path.isfile(path)
    if is_file:
        last_row = df[-1:]
        last_row.to_csv("data.csv", index=False, encoding="shift-jis", mode='a', header=False)
    else:
        df.to_csv('data.csv', encoding = 'shift-jis',  index=False)
    
    # df = df.iloc[1:, :]

    #Todo
    #タイムスタンプ
    #途中から再開
