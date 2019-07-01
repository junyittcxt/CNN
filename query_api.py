import numpy as np
import pandas as pd
import glob
import os
import re

import joblib
import keras

from cnn_method import *
from cnn_preproc_function import *
from inference_function import *

import pymysql.cursors
import pandas as pd
from dateutil import parser

def gen_connection():
    connection = pymysql.connect(host='192.168.1.110',
                                 user='cxtanalytics',
                                 password='3.1415cxt',
                                 db='machinelearning',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

def query_mysql(connection, dt, table, window = None):
    try: 
        with connection.cursor() as cursor:
            if window is None:
                sql = "select * from {tb} where Date <= '{dd}' order by Date;".format(tb = table, dd = dt)
            else:
                sql = "select * from {tb} where Date <= '{dd}' order by Date desc limit {w};".format(tb = table, dd = dt, w = window)
            cursor.execute(sql)
            result = cursor.fetchall()
            data_df = pd.DataFrame(result, columns = result[0].keys())
            data_df["Date"] = pd.to_datetime(data_df["Date"])
            data_df = data_df.sort_values("Date").set_index("Date")
        return data_df
    except Exception as err:
        print(err)
        return pd.DataFrame()


def get_path_dict(strategy_meta):
    main_dir = strategy_meta["Location"]
    b_dir = strategy_meta["B"]
    s_dir = strategy_meta["S"]
    asset_b = [j.strip() for j in strategy_meta["Asset_B"].split(",")]
    asset_s = [j.strip() for j in strategy_meta["Asset_S"].split(",")]

    PATH_DICT = dict()
    PATH_DICT["b"] = dict()
    PATH_DICT["s"] = dict()

    if not asset_b[0] == "-":
        for target in asset_b:
            d_dir = b_dir
            AM_path = os.path.join(main_dir, d_dir, "ASSETS_MODELS")
            target_asset_folder_name = [f for f in os.listdir(AM_path) if re.search("^{target}".format(target = target), f)][0]
            target_path = os.path.join(AM_path, target_asset_folder_name)

            scaler_path = glob.glob(os.path.join(target_path, "scaler.pkl"))[0]
            model_params_path = glob.glob(os.path.join(target_path, "MODEL_PARAMS.pkl"))[0]
            data_params_path = glob.glob(os.path.join(target_path, "DATA_PARAMS.pkl"))[0]
            model_path = glob.glob(os.path.join(target_path, "*.model"))[0]
            PATH_DICT["b"][target] = [scaler_path, data_params_path, model_params_path, model_path]

    if not asset_s[0] == "-":
        for target in asset_s:
            d_dir = s_dir
            AM_path = os.path.join(main_dir, d_dir, "ASSETS_MODELS")
            target_asset_folder_name = [f for f in os.listdir(AM_path) if re.search("^{target}".format(target = target), f)][0]
            target_path = os.path.join(AM_path, target_asset_folder_name)

            scaler_path = glob.glob(os.path.join(target_path, "scaler.pkl"))[0]
            model_params_path = glob.glob(os.path.join(target_path, "MODEL_PARAMS.pkl"))[0]
            data_params_path = glob.glob(os.path.join(target_path, "DATA_PARAMS.pkl"))[0]
            model_path = glob.glob(os.path.join(target_path, "*.model"))[0]
            PATH_DICT["s"][target] = [scaler_path, data_params_path, model_params_path, model_path]

    return PATH_DICT

def load_item_by_key(PATH_DICT, key, exclude_model = False):
    try:
        direction_key = key.split("_")[0]
        asset_key = key.split("_")[1]
        val2 = PATH_DICT[direction_key][asset_key]

        scaler = joblib.load(val2[0])
        DATA_PARAMS = joblib.load(val2[1])
        MODEL_PARAMS = joblib.load(val2[2])
        if exclude_model:
            model = None
        else:   
            model =  keras.models.load_model(val2[3], custom_objects=None, compile=False)
        return scaler, DATA_PARAMS, MODEL_PARAMS, model

    except Exception as err2:
        print("Error with key:", key)
        print(PATH_DICT)
        print(err2)



#must initialize keras/tensorflow session config first
def load_items(PATH_DICT):
    ALL_SCALERS = dict()
    ALL_DATA_PARAMS = dict()
    ALL_MODEL_PARAMS = dict()
    ALL_MODELS = dict()

    for key, val in PATH_DICT.items():
        for key2, val2 in val.items():
            newkey = "{k1}_{k2}".format(k1 = key, k2 = key2)
            print("Loading:", newkey)
            ALL_SCALERS[newkey] = joblib.load(val2[0])
            ALL_DATA_PARAMS[newkey] = joblib.load(val2[1])
            ALL_MODEL_PARAMS[newkey] = joblib.load(val2[2])
            ALL_MODELS[newkey] =  keras.models.load_model(val2[3], custom_objects=None, compile=False)

    return ALL_SCALERS, ALL_DATA_PARAMS, ALL_MODEL_PARAMS, ALL_MODELS

#load only one
def load_item_one(PATH_DICT, order, asset):
    path_list = PATH_DICT[order][asset]
    scaler = joblib.load(path_list[0])
    DATA_PARAMS = joblib.load(path_list[1])
    MODEL_PARAMS = joblib.load(path_list[2])
    model = keras.models.load_model(path_list[3], custom_objects=None, compile=False)
    return scaler, DATA_PARAMS, MODEL_PARAMS, model




def predict_signal(query_date, scaler, DATA_PARAMS, MODEL_PARAMS, model, connection = None, db_variant = None):
    if connection is None:
        connection = gen_connection()

    raw_data_file = DATA_PARAMS["raw_data_file"]
    TARGET_TO_PREDICT = DATA_PARAMS["TARGET_TO_PREDICT"]
    BREAKOUT_WINDOW = DATA_PARAMS["BREAKOUT_WINDOW"]
    SEQ_LEN = DATA_PARAMS["SEQ_LEN"]

    try:
        CLEAN_METHOD_X = DATA_PARAMS["CLEAN_METHOD_X"]
    except:
        print("CLEAN_METHOD_X default to breakout_only_x")
        CLEAN_METHOD_X = "breakout_only_x"

    #get mysql table name using raw_data_file
    timeframe = int(raw_data_file.split("_")[2])
    if db_variant is None:
        data_table = "db_{t}_min".format(t = str(timeframe))
    else:
        data_table = "db_{t}_min_{v}".format(t = str(timeframe), v = str(db_variant))
    print("data_table:", data_table)

    #Load accepted index
    accepted_index_file = "{t}_{target}.pkl".format(t = timeframe, target = TARGET_TO_PREDICT)
    accepted_index = joblib.load(os.path.join("MINUTE_INDEX", accepted_index_file))
    print("Loaded: accepted_index")

    #Get and Clean Data
    prev_nrows = 0
    nrows = 0
    factor = 3
    while nrows < SEQ_LEN:
        factor = factor + 1
        query_df = query_mysql(connection, dt = query_date, table = data_table, window = (BREAKOUT_WINDOW+SEQ_LEN)*factor)[6:]

        df = clean_data_x(query_df, TARGET_TO_PREDICT, BREAKOUT_WINDOW, CLEAN_METHOD_X, accepted_index)
        print(df.tail())
        df.dropna(inplace = True)

        nrows = df.shape[0]
        if not nrows == 0 and nrows == prev_nrows:
            return df.index[-1], 0, -1, "Not enough data."

        prev_nrows = nrows
        print("Data Preparation:", "0", "Factor:", factor, "Shape:", df.shape)


    print("Query: Done!")

    #Verify Latest Date
    if not df.index[-1] == parser.parse(query_date):
        return df.index[-1], 0, -1, "query_date does not match latest date in data."   #date, signal, error_code

    #Check Break in Date


    #Scaling
    target_col= "target"
    x_columns = [j for j in df.columns if j != target_col]
    df.loc[:,x_columns] = scaler.transform(df[x_columns])
    print("Scaling: Done!")

    #TimeSeriesGenerator
    X = df[x_columns].values
    Y = df[target_col].values
    data_gen = TimeseriesGenerator(X,Y,
                           length=SEQ_LEN, sampling_rate=1,
                           batch_size=128,
                           shuffle=False)

    #Prediction
    y_pred = model.predict_generator(data_gen)
    print("Predict: Done!")

    return df.index[-1], y_pred[-1][0], 1, "Successful."   #date, signal, error_code
