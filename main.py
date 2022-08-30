from re import A
import time
import pandas as pd
import requests
import json
import os
import configparser
from bitbank import Bitbank

jpy_balance = 100000 #日本円
btc_balance = 0 #btc数量

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

def buy(buy_price, amount=0.001):
    global jpy_balance
    global btc_balance 
    jpy_balance -= buy_price * amount
    btc_balance += amount 
    total_balance = jpy_balance + btc_balance * buy_price
    print(jpy_balance)
    print(btc_balance)
    print(total_balance)
    print('buy')



def sell(sell_price, amount=0.001):
    global jpy_balance
    global btc_balance 
    if btc_balance > 0:
        jpy_balance += sell_price * amount
        btc_balance -= amount
        total_balance = jpy_balance + btc_balance * sell_price
        print(jpy_balance)
        print(btc_balance)
        print(total_balance)
        print('sell!')
    else:
        print("スルー")

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

    if ticker in position.keys():
        if float(df['price'].iloc[-1]) > df['+2sigma'].iloc[-1]:
            # and bitbank.check_ex_rate(pair) < float(df['price'].iloc[-1])
            sell(float(df['price'].iloc[-1]))
            
        else:
            if float(df['price'].iloc[-1]) < df['-2sigma'].iloc[-1]:
                buy(float(df['price'].iloc[-1]))
            else:
                print("スルー")

    path = 'data.csv'
    is_file = os.path.isfile(path)
    if is_file:
        last_row = df[-1:]
        last_row.to_csv("data.csv", index=False, encoding="shift-jis", mode='a', header=False)
    else:
        df.to_csv('data.csv', encoding = 'shift-jis',  index=False)
    
    # df = df.iloc[1:, :]
