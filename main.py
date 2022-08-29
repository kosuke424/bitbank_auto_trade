import time
import pandas as pd
import requests
import json
import configparser
from bitbank import Bitbank

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
    print(df)

    df['SMA'] = df['price'].rolling(window=duration).mean()
    df['std'] = df['price'].rolling(window=duration).std()
    df['-2sigma'] = df['SMA'] - 2*df['std']
    df['+2sigma'] = df['SMA'] + 2*df['std']

    if ticker in position.keys():
        if float(df['price'].iloc[-1]) > df['+2sigma'].iloc[-1] and bitbank.check_ex_rate(pair) < float(df['price'].iloc[-1]):
            print('sell!')
        else:
            print("else")
            if float(df['price'].iloc[-1]) < df['-2sigma'].iloc[-1]:
                print("buy!")

df = df.iloc[1:, :]



