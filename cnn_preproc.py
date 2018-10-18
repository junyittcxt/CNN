
import optparse
import pandas as pd
import numpy as np
from sklearn import preprocessing
# import tensorflow as tf
import os, time, sys, sklearn
from sklearn.externals import joblib
from rnn_functions import *
import time
import datetime

# from keras.models import Sequential
# from keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D
# import keras
#
# import os
# os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
# os.environ["CUDA_VISIBLE_DEVICES"]="0"

optparser = optparse.OptionParser()
optparser.add_option("-f", "--first", default=1, help="First")
optparser.add_option("-i", "--index", default=2, help="index")
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
opts = optparser.parse_args()[0]
first = int(opts.first)
index = int(opts.index)
assetindex = int(opts.assetindex)

possible_asset = ['AUDUSD', 'EURUSD', 'EURGBP', 'EURJPY', 'EWH', 'EWZ', 'FXI', 'IAU', 'EZU', 'KRE', 'LQD', 'NZDUSD', 'EEM', 'EFA',
 'GDX', 'HYG', 'SPY', 'XLU', 'IYR', 'GLD', 'EWT', 'IEF', 'AGG', 'UNG', 'USDJPY', 'GBPUSD', 'USDCAD', 'SLV', 'RSX', 'EWJ', 'OIH',
 'SMH', 'XLB', 'TLT', 'USDCHF', 'USO', 'XLF', 'XLK', 'XLP', 'XOP', 'VEA', 'VWO', 'XLE', 'XLI', 'XLV', 'XRT', 'XLY', 'VNQ', 'EWW', 'XBI']

DATA_PARAMS = dict()
DATA_PARAMS["TARGET_TO_PREDICT"] = possible_asset[assetindex] #CHANGE THIS ONLY
print("====================================================")
print("ASSET:", DATA_PARAMS["TARGET_TO_PREDICT"])
print("====================================================")
DATA_PARAMS["FUTURE_PERIOD_PREDICT"] = 5
DATA_PARAMS["SEQ_LEN"] = 60
DATA_PARAMS["TARGET_THRESHOLD"] = 0.001

dirdata = os.path.join('cnn',DATA_PARAMS["TARGET_TO_PREDICT"])
init_dir(dirdata)


def load_data(DATA_PARAMS):
    # NROWS = DATA_PARAMS["NROWS"]
    TARGET_TO_PREDICT = DATA_PARAMS["TARGET_TO_PREDICT"]
    FUTURE_PERIOD_PREDICT = DATA_PARAMS["FUTURE_PERIOD_PREDICT"]
    SEQ_LEN = DATA_PARAMS["SEQ_LEN"]
    TARGET_THRESHOLD = DATA_PARAMS["TARGET_THRESHOLD"]

    #Load
    df = pd.read_csv("./DATA/x_82_ETF_FOREX_5MIN_RETONLY.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")

    #clean and create target
    df = filter_off_trading_day(df, target = TARGET_TO_PREDICT, threshold = 0.1)
    df = create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, cumulative_returns)
    df = classify_target(df, "target", TARGET_THRESHOLD, False)

    #split
    end_split = [datetime.datetime(2011,1,1), datetime.datetime(2012,1,1), datetime.datetime(2016,1,1), datetime.datetime(2018,1,1)]
    df_list = []
    for i,d in enumerate(end_split):
        if i== 0:
            df2 = df[df.index <= d]
            df_list.append(df2)
        else:
            df2 = df[(df.index <= d) & (df.index > end_split[i-1])]
            df_list.append(df2)


    startdates = [z.index[0] for z in df_list]
    enddates = [z.index[-1] for z in df_list]
    print(startdates)
    print(enddates)

    return df_list


def first_preproc(df_list, DATA_PARAMS):
    SEQ_LEN = DATA_PARAMS["SEQ_LEN"]
    TARGET_TO_PREDICT = DATA_PARAMS["TARGET_TO_PREDICT"]
    #Scaling
    scaler = sklearn.preprocessing.MinMaxScaler(feature_range = (0,1))

    train_x, train_y, train_t, scaler, x_columns, train_x_shape = preprocess_returns_df_cnn(df=df_list[0], target_col = "target", scaler = scaler, SEQ_LEN = SEQ_LEN, fit = True, same_prop = False, shuffle = True)
    val_x, val_y, val_t, _, _, _ = preprocess_returns_df_cnn(df=df_list[1], target_col = "target", scaler = scaler, SEQ_LEN = SEQ_LEN, fit = False, same_prop = False, shuffle = False)
#     test_x, test_y, test_t, _, _, _ = preprocess_returns_df_cnn(df=df_list[2], target_col = "target", scaler = scaler, SEQ_LEN = SEQ_LEN, fit = False, same_prop = False, shuffle = False)
    data_dir = os.path.join('cnn', TARGET_TO_PREDICT, 'data')
    init_dir(data_dir)
    joblib.dump(train_x, os.path.join(data_dir,'train_x.pkl'))
    joblib.dump(train_y, os.path.join(data_dir,'train_y.pkl'))
    joblib.dump(train_t, os.path.join(data_dir,'train_t.pkl'))
    joblib.dump(val_x, os.path.join(data_dir,'val_x.pkl'))
    joblib.dump(val_y, os.path.join(data_dir,'val_y.pkl'))
    joblib.dump(val_t, os.path.join(data_dir,'val_t.pkl'))

    joblib.dump(train_x_shape, os.path.join(data_dir,'train_x_shape.pkl'))
    joblib.dump(scaler, os.path.join(data_dir,'scaler.pkl'))
    joblib.dump(x_columns, os.path.join(data_dir,'x_columns.pkl'))
    joblib.dump(df_list, os.path.join(data_dir,'df_list.pkl'))
    joblib.dump(DATA_PARAMS, os.path.join(data_dir,'DATA_PARAMS.pkl'))

#     return train_x, train_y, train_t, val_x, val_y, val_t, scaler, x_columns, train_x_shape

def test_preproc(df_list, DATA_PARAMS, scaler, index = 2):
    SEQ_LEN = DATA_PARAMS["SEQ_LEN"]
    TARGET_TO_PREDICT = DATA_PARAMS["TARGET_TO_PREDICT"]
    test_dir = os.path.join('cnn', TARGET_TO_PREDICT, 'data', 'test')
    init_dir(test_dir)
    if index == 2:
        test_x, test_y, test_t, _, _, _ = preprocess_returns_df_cnn(df=df_list[2], target_col = "target", scaler = scaler, SEQ_LEN = SEQ_LEN, fit = False, same_prop = False, shuffle = False)
        joblib.dump(test_x, os.path.join(test_dir,'test_x.pkl'))
        joblib.dump(test_y, os.path.join(test_dir,'test_y.pkl'))
        joblib.dump(test_t, os.path.join(test_dir,'test_t.pkl'))
    elif index == 3:
        test2_x, test2_y, test2_t, _, _, _ = preprocess_returns_df_cnn(df=df_list[3], target_col = "target", scaler = scaler, SEQ_LEN = SEQ_LEN, fit = False, same_prop = False, shuffle = False)
        joblib.dump(test2_x, os.path.join(test_dir,'test2_x.pkl'))
        joblib.dump(test2_y, os.path.join(test_dir,'test2_y.pkl'))
        joblib.dump(test2_t, os.path.join(test_dir,'test2_t.pkl'))

if first == 1:
    df_list = load_data(DATA_PARAMS)
    first_preproc(df_list, DATA_PARAMS)
else:
    data_dir = os.path.join('cnn', DATA_PARAMS["TARGET_TO_PREDICT"], 'data')
    scaler=joblib.load(os.path.join(data_dir ,'scaler.pkl'))
    df_list=joblib.load(os.path.join(data_dir ,'df_list.pkl'))
    test_preproc(df_list, DATA_PARAMS, scaler, index)
