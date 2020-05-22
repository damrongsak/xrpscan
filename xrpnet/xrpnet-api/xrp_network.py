from transactions import *

ACCOUNT_ADDRESS = 'rPVMhWBsfF9iMXYj3aAzJVkPDTFNSyWdKy'

nodes = []
edges = []

df_account = get_account()
    
df_account.fillna('', inplace=True)
df_acc = df_account[['name', 'account', 'desc', 'XRP']
                    ].loc[df_account['name'] == 'Bittrex'].copy(deep=True)
df_acc['id'] = df_acc['account']
df_acc['label'] = df_acc['name'] + \
    '(' + df_acc['desc'] + ')'
df_acc['label'] = df_acc['label'].apply(lambda x: str(x).replace('()',''))
df_acc[['id', 'label']]

# Parrent Node
for _, row in df_acc[['id', 'label']].iterrows():
    nodes.append(dict(row))


def get_flow_in_out(ACCOUNT_ADDRESS):
    data = get_transactions(ACCOUNT_ADDRESS, days=10,
                            limit=100, descending=True)
    df_trans = convert_to_dataframe(ACCOUNT_ADDRESS, data)

    df_flow_in = pd.DataFrame()
    df_flow_out = pd.DataFrame()

    if df_trans.empty == False:
        # count & sum amount by flow IN/OUT
        df_flow_in = df_trans.loc[df_trans.Flow == 'IN'].groupby(
            ['From', 'From Desc', 'To', 'To Desc', 'DT'])['Amount'].agg(['count', "sum"])
        df_flow_in.sort_values('sum', ascending=False, inplace=True)

        df_flow_out = df_trans.loc[df_trans.Flow == 'OUT'].groupby(
            ['From', 'From Desc', 'To', 'To Desc', 'DT'])['Amount'].agg(['count', "sum"])
        df_flow_out.sort_values('sum', ascending=False, inplace=True)

    return df_flow_in, df_flow_out


def find_account(acc):
    for d in nodes:
        v = d['id'] if d['id'] == acc else False
        if v != False:
            return True
    return False

def xrpnet_account(acc_name):
    if len(acc_name) == 0:
        acc_name = 'Bittrex'
    
    df_account.fillna('', inplace=True)
    df_acc = df_account[['name', 'account', 'desc', 'XRP']
                        ].loc[df_account['name'] == acc_name].copy(deep=True)
    df_acc['id'] = df_acc['account']
    df_acc['label'] = df_acc['name'] + \
        '(' + df_acc['desc'] + ') XRP: ' + df_acc['XRP'].astype(str)
    df_acc[['id', 'label']]

    # Parrent Node
    df_acc['Account Already'] = df_acc['id'].apply(lambda x: find_account(x))
    df_accx = df_acc.loc[df_acc['Account Already'] == False]
    for _, row in df_accx[['id', 'label']].iterrows():
        nodes.append(dict(row))

    result = {
        'nodes': nodes,
        'edges': edges,
    }

    return result

def xrpnet(ACCOUNT_ADDRESS):
    df_flow_in, df_flow_out = get_flow_in_out(ACCOUNT_ADDRESS)

    # Flow IN Nodes
    if df_flow_in.empty == False:
        df_in = df_flow_in.reset_index(
        )[['From', 'From Desc', 'To', 'To Desc', 'DT', 'count', 'sum']]

        df_in['id'] = df_in['From'] + '-' + df_in['DT'].astype(str)
        df_in['label'] = ' To: ' + df_in['To Desc'] + \
            ' DT: ' + df_in['DT'].astype(str)

        df_in['From Already'] = df_in['From'].apply(lambda x: find_account(x))
        df_in['Tag Already'] = df_in['id'].apply(lambda x: find_account(x))
        df_in['Dest Already'] = df_in['To'].apply(lambda x: find_account(x))

        df_inx = df_in.loc[df_in['From Already'] == False]
        df_inx = df_inx[['From', 'From Desc']].rename(
            columns={'From': 'id', 'From Desc': 'label'})
        df_inx.drop_duplicates(subset="id", keep='first', inplace=True)
        if df_inx.empty == False:
            for index, row in df_inx[['id', 'label']].iterrows():
                nodes.append(dict(row))

        df_inx = df_in[['id', 'label']].loc[df_in['Tag Already'] == False]
        if df_inx.empty == False:
            for index, row in df_inx[['id', 'label']].iterrows():
                nodes.append(dict(row))

        df_inx = df_in.loc[df_in['Dest Already'] == False]
        df_inx = df_inx[['To', 'To Desc']].rename(
            columns={'To': 'id', 'To Desc': 'label'})
        df_inx.drop_duplicates(subset="id", keep='first', inplace=True)
        if df_inx.empty == False:
            for index, row in df_inx[['id', 'label']].iterrows():
                nodes.append(dict(row))

        # From to DT
        for _, row in df_in.iterrows():
            edges.append(
                {
                    "from": str(row['From']),
                    "to": '{}-{}'.format(row['From'], str(row['DT'])),
                    "label": row['To Desc'] + ' DT:' + str(row['DT']),
                    "color": {
                        "color": "green",
                        "highlight": "green"
                    },
                    "arrows": {
                        "from": {
                            "scaleFactor": "0.5",
                            "type": "circle"
                        }
                    }
                }
            )

        # DT to Dest
        for _, row in df_in.iterrows():
            edges.append(
                {
                    "from": '{}-{}'.format(row['From'], str(row['DT'])),
                    "to": str(row['To']),
                    "label": 'XRP:' + str(row['sum']),
                    "color": {
                        "color": "green",
                        "highlight": "green"
                    },
                    "arrows": {
                        "from": {
                            "scaleFactor": "0.5",
                            "type": "circle"
                        }
                    }
                }
            )

    # Flow OUT Nodes
    if df_flow_out.empty == False:
        df_out = df_flow_out.reset_index(
        )[['From', 'From Desc', 'To', 'To Desc', 'DT', 'count', 'sum']].head(10)

        df_out['id'] = df_out['To'] + '-' + df_out['DT'].astype(str)
        df_out['label'] = ' To: ' + df_out['To Desc'] + \
            ' DT: ' + df_out['DT'].astype(str)

        df_out['From Already'] = df_out['From'].apply(lambda x: find_account(x))
        df_out['Tag Already'] = df_out['id'].apply(lambda x: find_account(x))
        df_out['Dest Already'] = df_out['To'].apply(lambda x: find_account(x))

        df_outx = df_out.loc[df_out['From Already'] == False]
        df_outx = df_outx[['From', 'From Desc']].rename(
            columns={'From': 'id', 'From Desc': 'label'})
        df_outx.drop_duplicates(subset="id", keep='first', inplace=True)
        if df_outx.empty == False:
            for index, row in df_outx[['id', 'label']].iterrows():
                nodes.append(dict(row))

        df_outx = df_out[['id', 'label']].loc[df_out['Tag Already'] == False]
        if df_outx.empty == False:
            for index, row in df_outx[['id', 'label']].iterrows():
                nodes.append(dict(row))

        df_outx = df_out.loc[df_in['Dest Already'] == False]
        df_outx = df_outx[['To', 'To Desc']].rename(
            columns={'To': 'id', 'To Desc': 'label'})
        df_outx.drop_duplicates(subset="id", keep='first', inplace=True)
        if df_outx.empty == False:
            for index, row in df_outx[['id', 'label']].iterrows():
                nodes.append(dict(row))

        # From to DT
        for _, row in df_out.iterrows():
            edges.append(
                {
                    "from": str(row['From']),
                    "to": '{}-{}'.format(row['To'], str(row['DT'])),
                    "label": row['To Desc'] + ' DT:' + str(row['DT']),
                    "color": {
                        "color": "red",
                        "highlight": "red"
                    },
                    "arrows": {
                        "from": {
                            "scaleFactor": "0.5",
                            "type": "circle"
                        }
                    }
                }
            )

        # DT to Dest
        for _, row in df_out.iterrows():
            edges.append(
                {
                    "from": '{}-{}'.format(row['To'], str(row['DT'])),
                    "to": str(row['To']),
                    "label": 'XRP:' + str(row['sum']),
                    "color": {
                        "color": "red",
                        "highlight": "red"
                    },
                    "arrows": {
                        "from": {
                            "scaleFactor": "0.5",
                            "type": "circle"
                        }
                    }
                }
            )

    result = {
        'nodes': nodes,
        'edges': edges
    }

    return result
