import numpy as np
import pandas as pd
import glob
import os
import re
import datetime

import joblib
import keras


from cnn_method import *
from cnn_preproc_function import *
from inference_function import *
from query_api import *

import pymysql.cursors
import pandas as pd
from dateutil import parser



def create_replace_sql(training_code, order, asset, PATH_DICT, start_date, end_date, db_variant = None):
    table_name = "{variant}_{code}{order}_{asset}".format(variant = db_variant, code = training_code, order = order, asset = asset)
    table_name = table_name.lower()
    print("=====Running:", table_name, "=========")
    #load only one asset _ one order
    scaler, DATA_PARAMS, MODEL_PARAMS, model = load_item_one(PATH_DICT, order = order, asset = asset)
    #predict
    signal_df = batch_predict_signal(start_date, end_date, scaler, DATA_PARAMS, MODEL_PARAMS, model, window = None, connection = None, db_variant = db_variant)
    signal_df["Date"] = signal_df["Date"].astype("str")
    print("=====Done Signal:", table_name, "============")
    
    return signal_df, table_name

def update_sql(training_code, order, asset, PATH_DICT, start_date, end_date, engine = None, db_variant = None):
    if engine is None:
        #initialize mysql engine
        engine = create_engine("mysql://cxtanalytics:3.1415cxt@192.168.1.110/machinelearning")

    table_name = "{variant}_{code}{order}_{asset}".format(variant = db_variant, code = training_code, order = order, asset = asset)
    table_name = table_name.lower()
    print("=====Running:", table_name, "=========")
    #get start_date 
    sql_signal_df = pd.read_sql(table_name, con = engine)
    scaler, DATA_PARAMS, MODEL_PARAMS, model = load_item_one(PATH_DICT, order = order, asset = asset)
    minute_window = 60*15*(DATA_PARAMS["SEQ_LEN"])
    latest_sql_date = pd.to_datetime(sql_signal_df["Date"].iloc[-2:]).iloc[-1]
    start_date = latest_sql_date - datetime.timedelta(minutes = minute_window)
    end_date = None

    #predict
    signal_df = batch_predict_signal(start_date, end_date, scaler, DATA_PARAMS, MODEL_PARAMS, model, window = None, connection = None, db_variant = db_variant)
        
    #filter_signal_df
    if np.sum(signal_df["Date"] == latest_sql_date) == 0:
        print("Date is not the latest!", table_name,"not updated!")
        return pd.DataFrame(), table_name
            
    signal_df["Date"] = signal_df["Date"].astype("str")
    to_append_signal_df = signal_df.loc[~signal_df["Date"].isin(sql_signal_df["Date"]),:]
    print("=====Done Signal:", table_name, "============")
    
    return to_append_signal_df, table_name
    
    
    
def query_mysql_by_date(connection, start_date, end_date, table):
    with connection.cursor() as cursor:
        sql = "select * from {tb} where Date <= '{dd}' and Date >= '{dd2}' order by Date;".format(tb = table, dd = end_date, dd2 = start_date)
        cursor.execute(sql)
        result = cursor.fetchall()
        data_df = pd.DataFrame(result, columns = result[0].keys())
        data_df["Date"] = pd.to_datetime(data_df["Date"])
        data_df = data_df.sort_values("Date").set_index("Date")
    return data_df



#Set window to None to batch predict all
def batch_predict_signal(start_date, end_date, scaler, DATA_PARAMS, MODEL_PARAMS, model, window = None, connection = None, db_variant = None):
    if start_date is None:
        start_date = datetime.datetime(1900,1,1)
    if end_date is None:
        end_date = datetime.datetime(2100,12,31)
    #Initialize SQL connection
    if connection is None:
        connection = gen_connection()

    #Initialize DATA_PARAMS
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

    #Query and clean data
    try:
#         query_df = query_mysql(connection, dt = query_date, table = data_table, window = window)
        query_df = query_mysql_by_date(connection, start_date = start_date, end_date = end_date, table = data_table)
        df = clean_data_x(query_df, TARGET_TO_PREDICT, BREAKOUT_WINDOW, CLEAN_METHOD_X, accepted_index)
        df.dropna(inplace = True)
        print("Clean: Done!")
    except Exception as err:
        print("Error CleanData:", err)
        return -1

    nrow = df.shape[0]
    if nrow == 0:
        print("Error: nrow = 0")
        return -1
    elif nrow < SEQ_LEN:
        print("Error: nrow < SEQ_LEN")
        return -1

    #Time Series Generator (to feed data to model)
    df_data, timestamp, all_data_gen = FullTSGenerator(df.copy(), scaler, batch_size = 128, SEQ_LEN = SEQ_LEN, old = False)

    #Verify Latest Date
#     if not timestamp[-1] == query_date:
#         #         return timestamp[-1], 0, -1, "query_date does not match latest date in data."   #date, signal, error_code
#         print("Query Date mismatch!")

    #Prediction
    y_pred = model.predict_generator(all_data_gen)
    print("Predict: Done!")

    signal_df = pd.DataFrame(dict(Date = timestamp, signal_raw = np.array(y_pred).flatten()))

    return signal_df
