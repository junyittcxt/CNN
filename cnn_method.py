from cnn_preproc_function import *

import numpy as np
import pandas as pd
import sklearn
from sklearn import preprocessing
from sklearn.utils import class_weight
from sklearn.externals import joblib
from keras.preprocessing.sequence import TimeseriesGenerator

def load_data(raw_data_file):
    #Load
    df = pd.read_csv(raw_data_file)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    print("Load Data: Done!")

    return df

def load_data_daily_close_missing(raw_data_file, missing_threshold = 0.1):
    #Load
    df = pd.read_csv(raw_data_file)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    missing_threshold = 0.1
    u1 = df.apply(lambda x: np.mean(np.isnan(x)) < missing_threshold)
    df2 = df.loc[:, u1]
    df2.fillna(method = "ffill").dropna()
    rdf = df2.pct_change().dropna()
    print("Load Data: Done!")

    return rdf

def clean_and_create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION, TARGET_THRESHOLD, FLIP, filter_tradingday = True):
    #Clean and Create Target
    if filter_tradingday:
        df = filter_off_trading_day(df, target = TARGET_TO_PREDICT, threshold = 0.1)

    if TARGET_FUNCTION == "cumulative_returns":
        TARGET_FUNCTION_R = cumulative_returns
    try:
        df = create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION_R)
    except:
        df = create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION)
    df = classify_target(df, "target", TARGET_THRESHOLD, FLIP)
    print("Clean Data: Done!")

    return df

def split_df(df, end_split):
    #Split df and get index
    start_index, end_index = get_index_from_date(df, end_split)
    target_col= "target"
    x_columns = [j for j in df.columns if j != target_col]

    #Scaling
    # scaler = sklearn.preprocessing.MinMaxScaler(feature_range = (0,1))
    scaler = sklearn.preprocessing.StandardScaler()
    #Fit train_x
    train_x_data = df[x_columns].iloc[start_index[0]:(end_index[0]+1)].values
    scaler.fit(train_x_data)
    #Scale all
    df.loc[:,x_columns] = scaler.transform(df[x_columns])
    X = df[x_columns].values
    Y = df[target_col].values

    return df, X, Y, start_index, end_index, scaler



def TSGenerator(X, Y, SEQ_LEN, BATCH_SIZE, start_index, end_index):
    #Create TimeseriesGenerator
    train_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=True,
                                   start_index=start_index[0], end_index=end_index[0])
    val_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=False,
                                   start_index=start_index[1], end_index=end_index[1])
    test_1_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=False,
                                   start_index=start_index[2], end_index=end_index[2])
    test_2_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=False,
                                   start_index=start_index[3], end_index=end_index[3])
    shape_x = train_data_gen[0][0].shape
    print(shape_x)
    print("Number of batches per epoch:", len(train_data_gen))
    print("TSGenerator: Done!")

    return train_data_gen, val_data_gen, test_1_data_gen, test_2_data_gen, shape_x

def get_class_weights(df, start_index, end_index):
    #Calculate class_weights
    train_y = df["target"].iloc[start_index[0]:(end_index[0]+1)].values
    class_weights = class_weight.compute_class_weight('balanced',
                                                     np.unique(train_y),
                                                     train_y)
    print(class_weights)

    return class_weights

def save_var(DATA_PARAMS, MODEL_PARAMS, scaler, project_folder):
    joblib.dump(DATA_PARAMS, os.path.join(project_folder,'DATA_PARAMS.pkl'))
    joblib.dump(MODEL_PARAMS, os.path.join(project_folder,'MODEL_PARAMS.pkl'))
    joblib.dump(scaler, os.path.join(project_folder,'scaler.pkl'))
    print("Data Saved!")


########################
#INFERENCE
########################
def FullTSGenerator(df, scaler, batch_size, SEQ_LEN, old = False):
    #Split df and get index
    target_col= "target"
    x_columns = [j for j in df.columns if j != target_col]

    #Scale all
    if not old:
        df.loc[:,x_columns] = scaler.transform(df[x_columns])

    X = df[x_columns].values
    Y = df[target_col].values

    all_data_gen = TimeseriesGenerator(X, Y, length=SEQ_LEN, batch_size=batch_size, shuffle=False)
    timestamp = df.index[SEQ_LEN:]
    return df, timestamp, all_data_gen
