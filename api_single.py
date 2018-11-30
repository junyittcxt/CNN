import flask
from flask import request
import json
import pandas as pd
import numpy as np

import time
import optparse

import os, re
import tensorflow as tf
import keras
import joblib
from dateutil import parser

from query_api import *

app = flask.Flask(__name__)

@app.route('/test')
def test():
    return flask.jsonify(dict(u = 20, b=1))


@app.route('/user/<username>')
def show_user_profile(username):
    params = request.args
    str_data = str(params.get("date"))

    # show the user profile for that user
    return 'User {} {}'.format(str_data, username)


@app.route("/predict", methods=["GET","POST"])
def predict():
    try:
        #Get args
        params = request.args

        query_date = str(params.get("date"))

        return_dict = dict()
        #PREDICTIONS
        t0 = time.time()
        last_date, y_pred, error_code, error_message = predict_signal(query_date, scaler, DATA_PARAMS, MODEL_PARAMS, model, connection = connection)
        t1 = time.time()
        return_dict["last_date"] = last_date.strftime('%Y-%m-%d %H:%M:%S')

        return_dict["query_date"] = query_date
        return_dict["y"] = str(y_pred)
        return_dict["asset"] = asset
        return_dict["key"] = key
        return_dict["error_code"] = str(error_code)
        return_dict["error_message"] = error_message

        print(t1-t0, return_dict)

        # return str(y_pred)
        return flask.jsonify(return_dict)

    except Exception as err:
        print(err)
        err_dict = dict()
        err_dict["asset"] = asset
        err_dict["key"] = key
        err_dict["error_code"] = "-2"
        return_dict["error_message"] = err
        err_dict["y"] = "0"
        return flask.jsonify(err_dict)


if __name__ == "__main__":
    #Get args
    optparser = optparse.OptionParser()
    optparser.add_option("-s", "--strat", default="1202", help="strat")
    optparser.add_option("-k", "--key", default="b_EWW", help="key")
    optparser.add_option("-p", "--port", default=5050, help="port")
    optparser.add_option("-g", "--gpu", default="0", help="gpu")
    opts = optparser.parse_args()[0]
    strat = opts.strat
    key = opts.key
    port = opts.port
    gpu = str(opts.gpu)
    print("===========================")
    print("strat:", strat)
    print("key:", key)
    print("port:", port)
    print("===========================")

    # GPU initialization
    print("Initializing GPU...")
    # gpu = "1"
    os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ["CUDA_VISIBLE_DEVICES"]=gpu
    config = tf.ConfigProto()
    # config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 0.005
    session = tf.Session(config=config)

    #Load strategy_meta
    try:
        json_path = os.path.join("STRATEGY_META", "{}.json".format(strat))
        output_file = open(json_path).read()
        strategy_meta = json.loads(output_file)
        print("Doing Strategy: {}, Key: {}, Port: {}".format(strat, key, port))
    except Exception as err:
        print("Error at:", "Load strategy_meta")
        print(err)

    #Create MySQL Connection
    try:
        print("Connecting to MySQL Database...")
        connection = gen_connection()
    except Exception as err:
        print("Error at:", "Create MySQL Connection")
        print(err)


    #Initialize Model
    try:
        print("Initializing Model...")
        PATH_DICT = get_path_dict(strategy_meta)
        scaler, DATA_PARAMS, MODEL_PARAMS, model = load_item_by_key(PATH_DICT, key)
        asset = DATA_PARAMS["TARGET_TO_PREDICT"]
    except Exception as err:
        print("Error at:", "Initialize Model")
        print(err)


    print("testing!")
    query_date = "2018-11-26 12:00:00"
    aa = predict_signal(query_date, scaler, DATA_PARAMS, MODEL_PARAMS, model, connection)
    print("pred:", aa)

    app.run(host='0.0.0.0', port = port, debug=True, use_reloader=False)

    #Load scalers, model params, data params, and models
    # print("Loading Models...")
    # t0 = time.time()
    # ALL_SCALERS, ALL_DATA_PARAMS, ALL_MODEL_PARAMS, ALL_MODELS = load_items(PATH_DICT)
    # t1 = time.time()
    # print("Done:", t1-t0, "seconds!")
    #
