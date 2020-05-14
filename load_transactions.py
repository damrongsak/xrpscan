import pandas as pd
import requests
import json
from urllib.request import urlopen
from IPython.display import JSON
from pandas.io.json import json_normalize

from datetime import datetime
from datetime import timedelta
import time

# Config
prev_day = 90
limit_out_trans = 400
df_name = None

# Function


def load_account():
    df_name = pd.read_excel(
        'data/List of well-known Names used to identify accounts.xlsx')
    df_name = df_name.sort_values(by='XRP', ascending=False)
    df_name.fillna('', inplace=True)

    return df_name


def find_desc(account):
    try:
        _df = df_name.loc[df_name.account ==
                          account, ['name', 'desc']].astype(str)
        return '{}{}'.format(_df.name.values[0], '({})'.format(_df.desc.values[0]) if len(_df.desc.values[0]) > 0 else '')
    except:
        return 'Unknow'


def load_transactions(ACCOUNT_ADDRESS):
    start = datetime.now() - timedelta(days=prev_day)
    date_start = start.strftime("%Y-%m-%dT%H:%M:%SZ")

    end = datetime.now()
    date_end = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = 'https://data.ripple.com/v2/accounts/{ACCOUNT_ADDRESS}/transactions?start={date_start}&end={date_end}&type=Payment&result=tesSUCCESS&limit={limit}&descending=True'.format(
        ACCOUNT_ADDRESS=ACCOUNT_ADDRESS, date_start=date_start, date_end=date_end, limit=limit_out_trans)

    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    r = requests.get(url, headers=header)

    data = json.loads(r.text)

    return data


def convert_to_dataframe(account, data):
    if data['count'] == 0:
        return

    trans_list = []
    for d in data['transactions']:
        account_desc = ''
        d_date = d['date']
        d_hash = d['hash']
        d_tx_from = d['tx']['Account']
        d_tx_from_desc = ''
        d_tx_type = d['tx']['TransactionType']
        d_tx_flow = ''
        d_tx_to = d['tx']['Destination']
        d_tx_to_desc = ''
        d_tx_dt = d['tx']['DestinationTag'] if d['tx'].__contains__(
            'DestinationTag') else ''

        d_tx_amount = 0
        d_tx_currency = ''
        d_tx_issuer = ''
        if str(type(d['tx']['Amount'])) != "<class 'dict'>":
            d_tx_amount = float(d['tx']['Amount']) / 1000000
        else:
            d_tx_amount = float(d['tx']['Amount']['value']) / 1000000
            d_tx_currency = d['tx']['Amount']['currency'][0:8]
            d_tx_issuer = d['tx']['Amount']['issuer']

        d_meta_delivered_amount = 0
        if str(type(d['meta']['delivered_amount'])) != "<class 'dict'>":
            d_meta_delivered_amount = float(
                d['meta']['delivered_amount']) / 1000000
        else:
            d_meta_delivered_amount = float(
                d['meta']['delivered_amount']['value']) / 1000000

        d_tx_fee = float(d['tx']['Fee']) / 1000000
        d_meta_result = d['meta']['TransactionResult']

        trans_list.append([account, account_desc, d_date, d_hash, d_tx_from, d_tx_from_desc, d_tx_type, d_tx_flow, d_tx_to,
                           d_tx_to_desc, d_tx_dt, d_tx_amount, d_tx_currency, d_tx_issuer, d_meta_delivered_amount, d_tx_fee, d_meta_result])

    df_trans = pd.DataFrame(trans_list, columns=['account', 'Account Desc', 'Date', 'Tx hash', 'From', 'From Desc',
                                                 'Type', 'Flow', 'To', 'To Desc', 'DT', 'Amount', 'Currency', 'Issuer', 'Delivered Amount', 'Fee', 'Result'])

    df_trans['Account Desc'] = df_trans['account'].apply(
        lambda x: find_desc(x))
    df_trans['From Desc'] = df_trans['From'].apply(lambda x: find_desc(x))
    df_trans['To Desc'] = df_trans['To'].apply(lambda x: find_desc(x))
    df_trans['Flow'] = df_trans[['account', 'To']].apply(
        lambda x: 'IN' if x['account'] == x['To'] else 'OUT', axis=1)

    return df_trans


if __name__ == "__main__":
    today = datetime.now()
    date_process = today.strftime("%Y-%m-%dT%H:%M:%SZ")

    print('Start@{}'.format(date_process))

    frames = []
    df_name = load_account()

    # Fillter Wallet
    # df_name = df_name.loc[df_name['name'].str.contains('Binance')] # Binance Only
    df_name = df_name[:20]  # Top 20 XRP balance

    for _, row in df_name.iterrows():
        print('{}-{}-{}'.format(row['account'], row['name'], row['desc']))
        ACCOUNT_ADDRESS = row['account']
        data = load_transactions(ACCOUNT_ADDRESS)

        if data.__contains__('result'):
            if data['result'] == 'success' and data['count'] > 0:
                df_tran = convert_to_dataframe(ACCOUNT_ADDRESS, data)
                frames.append(df_tran)

    df_trans = pd.concat(frames)

    # Export to excel
    df_trans.to_excel(
        'data/{}-transactions.xlsx'.format(date_process[:10]), index=False)

    print('Done!')
