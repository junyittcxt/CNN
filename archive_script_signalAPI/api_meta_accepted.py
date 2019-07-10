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

import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = flask.Flask(__name__)

app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa4'

# def load_strat_key_port(strat):
#     # strat = "1202"
#     list_files = os.listdir(os.path.join("STRATEGY_KEYS_PORTS"))
#     print(list_files)
#     selected_csv = [j for j in list_files if j.split("-")[0] == strat][0]
#     df = pd.read_csv(os.path.join("STRATEGY_KEYS_PORTS", selected_csv))[["key", "port"]]
#
#     return df
#
#
# def get(port, payload, return_dict):
#     try:
#         r = requests.get('http://0.0.0.0:{}/predict'.format(port), params=payload)
#         print("port:", port, "status:", r)
#         port = str(port)
#         return_dict[port] = json.loads(r.text)
#     except Exception as err:
#         print("port:", port, "status:", "failed", err)
#         port = str(port)
#         return_dict[port] = dict(error_code = "-2", error_message = str(err), y = "0")
#





@app.route("/metadata", methods=["GET","POST"])
def metadata():
    params = request.args
    strat = str(params.get("strat"))
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('./Credential/DeepLearningAlphaC-666170c72205.json', scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open("TASK")

    # worksheet_list = spreadsheet.worksheets()
    worksheet = spreadsheet.worksheet("Accepted")

    # column_list = worksheet.range('A1:R1')
    task_df = pd.DataFrame(worksheet.get_all_records())
    task_df = task_df.astype(str)
    print(task_df)
    # print(task_df.Strategy == 1190)
    selected_task = task_df.loc[task_df.Strategy == strat]
    print(selected_task)
    out_dict = selected_task.to_dict("records")[0]
    print(out_dict)

    if len(out_dict["Asset_B"]) >= len(out_dict["Asset_S"]):
        out_dict["Asset"] = out_dict["Asset_B"]
    else:
        out_dict["Asset"] = out_dict["Asset_S"]

    return flask.jsonify(out_dict)
    # try:
    #     session["z"] = session["z"] + 1
    # except KeyError as KE:
    #     print(KE)
    #     session["z"] = 100
    # return str(session["z"])
#
# @app.route("/multi", methods=["GET","POST"])
# def multi():
#     #Get args
#     params = request.args
#     query_date = str(params.get("date"))
#     strat = str(params.get("strat"))
#
#     key_port_df = load_strat_key_port(strat)
#
#     t0 = time.time()
#     jobs = []
#     manager = mp.Manager()
#     return_dict = manager.dict()
#     payload = {'date': query_date}
#     for port in key_port_df["port"]:
#         p = mp.Process(target=get, args=(port, payload, return_dict))
#         jobs.append(p)
#         p.start()
#
#     for proc in jobs:
#         proc.join()
#
#     t1 = time.time()
#     print("Time Elapsed:", t1-t0, "seconds")
#
#     rd = return_dict.copy()
#     out_df = pd.DataFrame.from_dict(rd, orient="index")
#     out_df.index.name = 'port'
#     out_df = out_df.reset_index().set_index("key")
#     out_dict = out_df.to_dict("index")
#     print(out_dict)
    # print(rd)
    # print(out_df)
    # print(out_dict)


    # return flask.jsonify(out_dict)


if __name__ == "__main__":

    app.run(host='0.0.0.0', port = 5004, debug=True, use_reloader=False)
