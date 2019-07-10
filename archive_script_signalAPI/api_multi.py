import gspread
from oauth2client.service_account import ServiceAccountCredentials
import optparse
from query_api import *

import time
import numpy as np
import requests
from multiprocessing import Pool
import multiprocessing as mp
import json
import flask
from flask import request, session
import glob, os
import pandas as pd

app = flask.Flask(__name__)

app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa4'

def load_strat_key_port(strat):
    # strat = "1202"
    list_files = os.listdir(os.path.join("STRATEGY_KEYS_PORTS"))
    print(list_files)
    selected_csv = [j for j in list_files if j.split("-")[0] == strat][0]
    df = pd.read_csv(os.path.join("STRATEGY_KEYS_PORTS", selected_csv))[["key", "port"]]

    return df


def get(port, payload, return_dict):
    try:
        r = requests.get('http://0.0.0.0:{}/predict'.format(port), params=payload)
        print("port:", port, "status:", r)
        port = str(port)
        return_dict[port] = json.loads(r.text)
    except Exception as err:
        print("port:", port, "status:", "failed", err)
        port = str(port)
        return_dict[port] = dict(error_code = "-2", error_message = str(err), y = "0")

def get_ports(strat):
    try:
        #Get Strategy Meta from Google Sheet instead of json
        scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name('/media/workstation/Storage/GoogleProject/DeepLearningAlphaC.txt', scope)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open("TASK")
        worksheet_list = spreadsheet.worksheets()
        Accepted = spreadsheet.worksheet("Accepted").get_all_records()
        adf = pd.DataFrame(Accepted)
        adf = adf.astype("str")

        #Select a strat, and get strategy_meta from TASK.Accepted sheet
        strategy_meta = adf.loc[adf.Strategy == strat].to_dict(orient = "records")[0]
        print("Load Strategy Meta: {}, Code: {}, Asset_B: {}, Asset_S: {}".format(strategy_meta["Strategy"],strategy_meta["Code"],strategy_meta["Asset_B"],strategy_meta["Asset_S"]))
    except Exception as err:
        print("Error at:", "Load strategy_meta")
        print(err)

    PATH_DICT = get_path_dict(strategy_meta)
    all_keys = []
    for k1, v1 in PATH_DICT.items():
        for k2,v2 in v1.items():
            all_keys.append("{}_{}".format(k1, k2))

    portstart = int(strategy_meta["port_start"])
    strats = [strat]*len(all_keys)
    keys = all_keys
    ports = np.arange(len(all_keys)) + portstart
    return ports



@app.route("/test", methods=["GET","POST"])
def test():
    ZZ = 6
    return str(ZZ)
    # try:
    #     session["z"] = session["z"] + 1
    # except KeyError as KE:
    #     print(KE)
    #     session["z"] = 100
    # return str(session["z"])

@app.route("/multi", methods=["GET","POST"])
def multi():
    #Get args
    params = request.args
    query_date = str(params.get("date"))
    strat = str(params.get("strat"))
    dbv = str(params.get("dbv"))

    # key_port_df = load_strat_key_port(strat)
    # ports = key_port_df["port"]

    ports = get_ports(strat)

    t0 = time.time()
    jobs = []
    manager = mp.Manager()
    return_dict = manager.dict()
    payload = {'date': query_date, "dbv": dbv}
    for port in ports:
        p = mp.Process(target=get, args=(port, payload, return_dict))
        jobs.append(p)
        p.start()

    for proc in jobs:
        proc.join()

    t1 = time.time()
    print("Time Elapsed:", t1-t0, "seconds")

    rd = return_dict.copy()
    out_df = pd.DataFrame.from_dict(rd, orient="index")
    out_df.index.name = 'port'
    out_df = out_df.reset_index().set_index("key")
    out_dict = out_df.to_dict("index")
    print(out_dict)
    # print(rd)
    # print(out_df)
    # print(out_dict)


    return flask.jsonify(out_dict)


if __name__ == "__main__":

    app.run(host='0.0.0.0', port = 5005, debug=True, use_reloader=False)
