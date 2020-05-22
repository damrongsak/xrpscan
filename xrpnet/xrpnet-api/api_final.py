from flask import Flask
from flask_cors import CORS
from flask import request, jsonify
import sqlite3
from transactions import *
from xrp_network import *

# Original source code from : https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["DEBUG"] = True

df_account = get_account()

@app.route('/', methods=['GET'])
def home():
    return '''<h1>XRP Scan API</h1>
<p>A prototype API for get XRP infomation.</p>'''

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/api/v1/account', methods=['GET'])
def api_account_info():
    query_parameters = request.args

    ACCOUNT_ADDRESS = query_parameters.get('account')
    df = get_account_info(ACCOUNT_ADDRESS)

    result = {}
    for index, row in df.iterrows():
        result[index] = dict(row)

    return jsonify(result)

@app.route('/api/v1/transactions/all', methods=['GET'])
def api_transactions_all():
    query_parameters = request.args

    ACCOUNT_ADDRESS = query_parameters.get('account')

    data = get_transactions(ACCOUNT_ADDRESS, days=30,
                            limit=400, descending=True)
    df_trans = convert_to_dataframe(ACCOUNT_ADDRESS, data)

    result = {}
    if df_trans.empty == False:
        for index, row in df_trans.iterrows():
            result[index] = dict(row)

    return jsonify(result)


@app.route('/api/v1/transactions/in', methods=['GET'])
def api_transactions_in():
    query_parameters = request.args

    ACCOUNT_ADDRESS = query_parameters.get('account')

    data = get_transactions(ACCOUNT_ADDRESS, days=10,
                            limit=100, descending=True)
    df_trans = convert_to_dataframe(ACCOUNT_ADDRESS, data)
    if df_trans.empty == False:
        # count & sum amount by flow IN/OUT
        df_flow_in = df_trans.loc[df_trans.Flow == 'IN'].groupby(
            ['From', 'From Desc', 'To', 'To Desc', 'DT'])['Amount'].agg(['count', 'sum'])
        df_flow_in.sort_values('sum', ascending=False, inplace=True)
    
    result = {}
    if df_flow_in.empty == False:
        df_flow_in.reset_index(inplace=True)
        for index, row in df_flow_in.iterrows():
            result[index] = dict(row)

    return jsonify(result)

@app.route('/api/v1/transactions/out', methods=['GET'])
def api_transactions_out():
    query_parameters = request.args

    ACCOUNT_ADDRESS = query_parameters.get('account')

    data = get_transactions(ACCOUNT_ADDRESS, days=10,
                            limit=100, descending=True)
    df_trans = convert_to_dataframe(ACCOUNT_ADDRESS, data)
    if df_trans.empty == False:
        # count & sum amount by flow IN/OUT
        df_flow_out = df_trans.loc[df_trans.Flow == 'OUT'].groupby(
            ['From', 'From Desc', 'To', 'To Desc', 'DT'])['Amount'].agg(['count', "sum"])
        df_flow_out.sort_values('sum', ascending=False, inplace=True)
    
    result = {}
    if df_flow_out.empty == False:
        df_flow_out.reset_index(inplace=True)
        for index, row in df_flow_out.iterrows():
            result[index] = dict(row)

    return jsonify(result)

@app.route('/api/v1/xrp/net', methods=['GET'])
def api_xrpnet():
    query_parameters = request.args

    ACCOUNT_ADDRESS = query_parameters.get('account')
    result = xrpnet(ACCOUNT_ADDRESS)

    return jsonify(result)

@app.route('/api/v1/xrp/net/account', methods=['GET'])
def api_xrpnet_account():
    query_parameters = request.args

    acc_name = query_parameters.get('account')
    result = xrpnet_account(acc_name)

    return jsonify(result)

@app.route('/api/v1/xrp/net/file', methods=['GET'])
def api_xrpnet_file():
    query_parameters = request.args

    ACCOUNT_ADDRESS = query_parameters.get('account')
    result = xrpnet(ACCOUNT_ADDRESS)
    with open('../xrpnet-ui/data/test.json', 'w') as json_file:
        json.dump(result, json_file)
    return jsonify(result)

if __name__ == "__main__":
    app.run()