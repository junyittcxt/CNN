import os
import time
import json
import joblib
import datetime
import numpy as np
import pandas as pd
from dateutil import parser
from cnn_method import clean_data_x
from keras.preprocessing.sequence import TimeseriesGenerator
from query_api import get_path_dict, gen_connection, load_item_by_key, query_mysql
from mongo_functions import get_portfolio_db

def timer(func):
    def inner(*args,**kwargs):
        t0 = time.time()
        out = func(*args,**kwargs)
        t1 = time.time()
        k =  t1 - t0
        print("Time elapsed: {} hours {} minutes {} seconds".format(int(k // 3600), int(k % 3600 // 60), int(k % 60)))
        return out
    return inner

@timer
def write_signal_mongo(query_date, PATH_DICT, key, strategy_meta, db = None, collection_name = "FirstDL", price_db = "Production", price_coll = "prices"):
    if db is None:
        db = get_portfolio_db()
    signal = get_signal_mongo(query_date, PATH_DICT, key, price_db, price_coll)
    signal["code"] = strategy_meta["Code"]
    signal["key"] = key
    signal["write_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db[collection_name].insert(signal)
           
        
def get_signal_mongo(query_date, PATH_DICT, key, price_db = "Production", price_coll = "prices"):
    try:
        output = None
        
        # Load scaler, PARAMS, model
        scaler, DATA_PARAMS, MODEL_PARAMS, model = load_item_by_key(PATH_DICT, key, exclude_model = True)
        print("Loaded: scaler, DATA_PARAMS, MODEL_PARAMS, model.")

        # Initialize parameters
        raw_data_file = DATA_PARAMS["raw_data_file"]
        TARGET_TO_PREDICT = DATA_PARAMS["TARGET_TO_PREDICT"]
        BREAKOUT_WINDOW = DATA_PARAMS["BREAKOUT_WINDOW"]
        SEQ_LEN = DATA_PARAMS["SEQ_LEN"]
        timeframe = int(raw_data_file.split("_")[2])
        try:
            CLEAN_METHOD_X = DATA_PARAMS["CLEAN_METHOD_X"]
        except:
            print("CLEAN_METHOD_X default to breakout_only_x")
            CLEAN_METHOD_X = "breakout_only_x"

        # Load accepted index
        accepted_index_file = "{t}_{target}.pkl".format(t = timeframe, target = TARGET_TO_PREDICT)
        accepted_index = joblib.load(os.path.join("MINUTE_INDEX", accepted_index_file))
        print("Loaded: MINUTE_INDEX for {}".format(TARGET_TO_PREDICT))
        
        # Get and Clean Data
        # Prices from MongoDB
        diff_seconds = max((BREAKOUT_WINDOW+SEQ_LEN)*5*timeframe*60, int(4*24*60*60))
        d2 = query_date
        d1 = d2 - datetime.timedelta(days = 0, seconds = diff_seconds)
        print("Using Mongo: ", d1, d2)
            
        prod_db = get_portfolio_db(price_db)
        coll = prod_db[price_coll]
        result = coll.find({"time": {"$gte": d1, "$lte": d2}})
        price_df = pd.DataFrame([j for j in result])
        price_df["name"] = price_df["name"].str.replace('@', '')
        price_df = price_df.pivot(index='time', columns='name', values='price')
        price_df = price_df.reset_index()
        price_df = price_df.rename(columns={"time": "Date"})
        price_df = price_df.set_index("Date")
        print(price_df.head(10))
        price_df = price_df.resample("{}min".format(timeframe), how = "last",label='right', closed = "right")
            
        ##FILTER COLUMNS
        data_columns_file = "MIN_{t}_COLUMNS.pkl".format(t = timeframe)
        data_columns = joblib.load(os.path.join("DATA_COLUMNS", data_columns_file))
        price_df = price_df[data_columns]
            
        price_df = price_df.ffill(axis = 0)
        price_df = price_df.bfill(axis = 0)
        
        df = clean_data_x(price_df, TARGET_TO_PREDICT, BREAKOUT_WINDOW, CLEAN_METHOD_X, accepted_index)
        df.dropna(inplace = True)
        
        if df.shape[0] == 0:
            output = price_df.index[-1], 0, -3, "Error: Not enough data."  
            prediction_dict = create_prediction_dict(output, query_date, timeframe)
            return prediction_dict

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
        print("TimeseriesGenerator: Done!")

        #Prediction
        while True:
            try:
                scaler, DATA_PARAMS, MODEL_PARAMS, model = load_item_by_key(PATH_DICT, key, exclude_model = False)
                print("Model Loaded!")
                y_pred = model.predict_generator(data_gen)
                print("Predict: Done!")
            except Exception as err:
                print("MODEL ERROR HERE: ", err)
                continue
            break

       
        diff_time = df.index[-1] - query_date
        if np.absolute(diff_time.total_seconds()/60) < timeframe:
            output = df.index[-1], y_pred[-1][0], 1, "Successful."   #date, signal, error_code
        else:
            output = df.index[-1], y_pred[-1][0], -2, "Outdated Signal."  
        
        
        prediction_dict = create_prediction_dict(output, query_date, timeframe)
        print(key, prediction_dict)
        return prediction_dict
    
    except Exception as err_all:
        print("Error at get_signal: ", err_all)
        return None
    

def create_prediction_dict(output, query_date, timeframe):
    prediction_dict = dict()
    prediction_dict["last_date"] = output[0].strftime('%Y-%m-%d %H:%M:%S')
    prediction_dict["query_date"] = query_date.strftime('%Y-%m-%d %H:%M:%S')
    prediction_dict["y"] = float(output[1])
    prediction_dict["status_code"] = int(output[2])
    prediction_dict["status"] = output[3]
    prediction_dict["timeframe"] = timeframe
    return prediction_dict