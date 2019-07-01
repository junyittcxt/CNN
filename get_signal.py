import os
import time
import json
import joblib
import numpy as np
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
def write_signal(query_date, db_variant, PATH_DICT, key, strategy_meta, db = None, collection_name = "FirstDL"):
    if db is None:
        db = get_portfolio_db()
    signal = get_signal(query_date, db_variant, PATH_DICT, key)
    signal["code"] = strategy_meta["Code"]
    signal["key"] = key
    db[collection_name].insert(signal)

def get_signal(query_date, db_variant, PATH_DICT, key):
    try:
        output = None
        print("Using Price Data from DB_VARIANT:", db_variant)

        # Load scaler, PARAMS, model
        scaler, DATA_PARAMS, MODEL_PARAMS, model = load_item_by_key(PATH_DICT, key, exclude_model = True)
        print("Loaded: scaler, DATA_PARAMS, MODEL_PARAMS, model.")

        # Initialize MySQL Connection
        mysql_connection = gen_connection()

        # Initialize parameters
        raw_data_file = DATA_PARAMS["raw_data_file"]
        TARGET_TO_PREDICT = DATA_PARAMS["TARGET_TO_PREDICT"]
        BREAKOUT_WINDOW = DATA_PARAMS["BREAKOUT_WINDOW"]
        SEQ_LEN = DATA_PARAMS["SEQ_LEN"]
        try:
            CLEAN_METHOD_X = DATA_PARAMS["CLEAN_METHOD_X"]
        except:
            print("CLEAN_METHOD_X default to breakout_only_x")
            CLEAN_METHOD_X = "breakout_only_x"

        # Get MySQL table name using raw_data_file
        timeframe = int(raw_data_file.split("_")[2])
        data_table = "db_{t}_min_{v}".format(t = str(timeframe), v = str(db_variant))
        print("Using MySQL Table:", data_table)

        # Load accepted index
        accepted_index_file = "{t}_{target}.pkl".format(t = timeframe, target = TARGET_TO_PREDICT)
        accepted_index = joblib.load(os.path.join("MINUTE_INDEX", accepted_index_file))
        print("Loaded: MINUTE_INDEX for {}".format(TARGET_TO_PREDICT))

        #Get and Clean Data
        prev_nrows = 0
        nrows = 0
        factor = 5
        while nrows < SEQ_LEN:
            factor = factor + 1
            query_length = max((BREAKOUT_WINDOW+SEQ_LEN)*factor, int(4*24*60/timeframe))
            query_df = query_mysql(mysql_connection, dt = query_date, table = data_table, window = query_length)
            query_df = query_df.bfill(axis = 0)
            query_df = query_df.ffill(axis = 0)

            if query_df.shape[0] == 0:
                output = df.index[-1], 0, -1, "Not enough data: 0 row."
                prediction_dict = create_prediction_dict(output, query_date)
                return prediction_dict
                break

            df = clean_data_x(query_df, TARGET_TO_PREDICT, BREAKOUT_WINDOW, CLEAN_METHOD_X, accepted_index)
            df.dropna(inplace = True)

            nrows = df.shape[0]
            if nrows == prev_nrows:
                print("df shape: ", df.shape)
                output =  df.index[-1], 0, -1, "Not enough data."
                prediction_dict = create_prediction_dict(output, query_date)
                return prediction_dict
                break
            prev_nrows = nrows
            print("Data Preparation:", "0", ", Factor:", factor, ", Shape:", df.shape)

        print("Query and Clean: Done!")

        #Verify Latest Date
    #     if not df.index[-1] == parser.parse(query_date):
#         if not df.index[-1] == query_date:
#             output = df.index[-1], 0, -1, "query_date does not match latest date in data."  

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
        
        
        prediction_dict = create_prediction_dict(output, query_date)
        print(key, prediction_dict)
        return prediction_dict
    
    except Exception as err_all:
        print("Error at get_signal: ", err_all)
        return None
    

def create_prediction_dict(output, query_date):
    prediction_dict = dict()
    prediction_dict["last_date"] = output[0].strftime('%Y-%m-%d %H:%M:%S')
    prediction_dict["query_date"] = query_date.strftime('%Y-%m-%d %H:%M:%S')
    prediction_dict["y"] = float(output[1])
    prediction_dict["status_code"] = int(output[2])
    prediction_dict["status"] = output[3]
    return prediction_dict