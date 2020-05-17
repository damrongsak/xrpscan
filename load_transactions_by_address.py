import os
import pandas as pd
import matplotlib.pyplot as plt

import requests
import json
from urllib.request import urlopen
from IPython.display import JSON
from pandas.io.json import json_normalize

from datetime import datetime
from datetime import timedelta

import time

df_account = None

# Function Save to excel with multiple sheet


def DF_TO_EXCEL_MUL(dfs, filename):
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    for sheetname, df in dfs.items():  # loop through `dict` of dataframes
        df.to_excel(writer, sheet_name=sheetname)  # send df to writer
        worksheet = writer.sheets[sheetname]  # pull worksheet object
        for idx, col in enumerate(df):  # loop through all columns
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),  # len of largest item
                len(str(series.name))  # len of column name/header
            )) + 1  # adding a little extra space
            worksheet.set_column(idx, idx, max_len)  # set column width
    writer.save()

# Load Account Name


def get_account():
    df_account = pd.read_excel(
        'data/List of well-known Names used to identify accounts.xlsx')
    df_account.fillna('', inplace=True)
    df_account = df_account.sort_values(by='XRP', ascending=False)
    return df_account

# Find Account Description


def find_account_desc(account):
    if not dir().count('df_account'):
        df_account = get_account()

    try:
        _df = df_account.loc[df_account.account ==
                             account, ['name', 'desc']].astype(str)
        return '{}{}'.format(_df.name.values[0], '({})'.format(_df.desc.values[0]) if len(_df.desc.values[0]) > 0 else '')
    except:
        return 'Unknow'

# Get account balances


def get_balances(ACCOUNT_ADDRESS, days=90):
    now = datetime.now() - timedelta(days=days)
    date_time = now.strftime("%Y-%m-%d")
    trans_list = []

    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    for i in range(1, days+2):

        date_time = now.strftime("%Y-%m-%d")

        url = 'https://data.ripple.com/v2/accounts/{ACCOUNT_ADDRESS}/balances?currency=XRP&date={date_time}T00:00:00Z&limit=3'.format(
            ACCOUNT_ADDRESS=ACCOUNT_ADDRESS, date_time=date_time)
        r = requests.get(url, headers=header)
        data = json.loads(r.text)

        if data['result'] != 'error':
            value = float(data['balances'][0]['value'])
            trans_list.append([ACCOUNT_ADDRESS, date_time, value])

        now = now + timedelta(days=1)

    df_balance = pd.DataFrame(
        trans_list, columns=['Account', 'Date', 'Balance'])
    df_balance.set_index(['Date'], inplace=True)

    return df_balance

# Get transactions


def get_transactions(ACCOUNT_ADDRESS, days, limit, descending):
    start = datetime.now() - timedelta(days=days)
    date_start = start.strftime("%Y-%m-%dT%H:%M:%SZ")

    end = datetime.now()
    date_end = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = 'https://data.ripple.com/v2/accounts/{ACCOUNT_ADDRESS}/transactions?start={date_start}&end={date_end}&type=Payment&result=tesSUCCESS&limit={limit}&descending={descending}'.format(
        ACCOUNT_ADDRESS=ACCOUNT_ADDRESS, date_start=date_start, date_end=date_end, limit=limit, descending=descending)

    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    r = requests.get(url, headers=header)
    data = json.loads(r.text)

    return data

# Convert JSON to DataFrame


def convert_to_dataframe(account, data):
    if data['result'] == "error":
        print(data['message'])
        return

    if data['count'] == 0:
        print('Data not found!')
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
        lambda x: find_account_desc(x))
    df_trans['From Desc'] = df_trans['From'].apply(
        lambda x: find_account_desc(x))
    df_trans['To Desc'] = df_trans['To'].apply(lambda x: find_account_desc(x))
    df_trans['Flow'] = df_trans[['account', 'To']].apply(
        lambda x: 'IN' if x['account'] == x['To'] else 'OUT', axis=1)

    return df_trans


def get_account_info(ACCOUNT_ADDRESS):
    url = 'https://api.xrpscan.com/api/v1/account//{ACCOUNT_ADDRESS}'.format(
        ACCOUNT_ADDRESS=ACCOUNT_ADDRESS)

    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    r = requests.get(url, headers=header)
    data = json.loads(r.text)

    acc_list = {'account': [data['account']], 'accountName': ['{}{}'.format(data['accountName']['name'], '({})'.format(data['accountName']['desc']) if len(data['accountName']['desc']) > 0 else '') if data['accountName'] != None else 'Unknow'], 'parent': [
        data['parent']], 'parentName': [data['parentName']['name'] if data['parentName'] != None else ''], 'inception': [data['inception']], 'initial_balance': [data['initial_balance']], 'xrpBalance': [float(data['xrpBalance'])], 'Note': ''}
    df_account_info = pd.DataFrame(acc_list, columns=[
                                   'account', 'accountName', 'parent', 'parentName', 'inception', 'initial_balance', 'xrpBalance', 'Note'])

    return df_account_info


if __name__ == "__main__":

    date_time = datetime.now().strftime("%Y-%m-%d")

    # get account info
    ACCOUNT_ADDRESS = 'rEy8TFcrAPvhpKrwyrscNYyqBGUkE9hKaJ'

    print('get account info: {}'.format(ACCOUNT_ADDRESS))
    df_account_info = get_account_info(ACCOUNT_ADDRESS)
    ac_list = []
    for c in list(df_account_info):
        ac_list.append([c, df_account_info[c].values[0]])

    cols = ['desc', 'info']
    df_account_info_x = pd.DataFrame(ac_list, columns=cols)
    df_account_info_x.set_index('desc', inplace=True)

    account_name = df_account_info['accountName'].values[0]

    # get account balance
    print('get balance')
    df_balance = get_balances(ACCOUNT_ADDRESS, 30)
    df_balance['Account Desc'] = df_balance['Account'].apply(
        lambda x: find_account_desc(x))

    print('get transactions')
    # get top 1000 transactions
    if not dir().count('df_account'):
        df_account = get_account()

    data = get_transactions(ACCOUNT_ADDRESS, days=300,
                            limit=1000, descending=True)
    df_trans = convert_to_dataframe(ACCOUNT_ADDRESS, data)
    if df_trans.empty == False:
        # count & sum amount by flow IN/OUT
        df_flow_in = df_trans.loc[df_trans.Flow == 'IN'].groupby(
            ['From', 'From Desc', 'To', 'To Desc', 'DT'])['Amount'].agg(['count', "sum"])
        df_flow_in.sort_values('sum', ascending=False, inplace=True)

        df_flow_out = df_trans.loc[df_trans.Flow == 'OUT'].groupby(
            ['From', 'From Desc', 'To', 'To Desc', 'DT'])['Amount'].agg(['count', "sum"])
        df_flow_out.sort_values('sum', ascending=False, inplace=True)

    dfs = {}
    if len(df_account_info_x) > 0:
        dfs.update({'account_info': df_account_info_x})
    if len(df_balance) > 0:
        dfs.update({'balance': df_balance})
    if df_trans.empty == False:
        dfs.update({'transactions': df_trans})
        if len(df_flow_in) > 0:
            dfs.update({'flow_in': df_flow_in})
        if len(df_flow_out) > 0:
            dfs.update({'flow_out': df_flow_out})

    filename = 'data/{}-TAG_FLOW-{}-{}.xlsx'.format(
        date_time, account_name, ACCOUNT_ADDRESS)
    DF_TO_EXCEL_MUL(dfs, filename)
    print('Export to: {}'.format(filename))

    # display account balance
    df_balance[['Balance']].plot(grid=True, figsize=(12, 5))
    plt.suptitle('TAG: {} - Name: {} - Balance: {}'.format(ACCOUNT_ADDRESS,
                                                           account_name, df_balance['Balance'].tail(1).values[0]))
    plt.xticks(rotation=45)
    plt.show()

    print('Done!')
