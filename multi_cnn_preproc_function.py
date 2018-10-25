from cnn_method import *
from cnn_preproc_function import *

import optparse
import numpy as np
import pandas as pd

import sklearn
from sklearn import preprocessing

import keras
import tensorflow as tf

from keras_model_configuration import *
from keras_metric import *

import datetime
import time
import os


def multi_create_target(df, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION, TARGET_THRESHOLD, FLIP, selected_cols = None):
    if TARGET_FUNCTION == "cumulative_returns":
        TARGET_FUNCTION_R = cumulative_returns

    if selected_cols is None:
        selected_cols = df.columns.values

    y_columns = []
    for target_col in selected_cols:
        if target_col in df.columns:
            new_target_col = "target_" + target_col
            y_columns.append(new_target_col)
            #Transform target
            df.loc[:,new_target_col] = df[target_col].rolling(window = FUTURE_PERIOD_PREDICT).apply(lambda x: TARGET_FUNCTION_R(x), raw=False)
            #Shift target
            df.loc[:,new_target_col] = df[new_target_col].shift(-FUTURE_PERIOD_PREDICT+1)
            #Classify target to binary
            df.loc[:,new_target_col] = df[new_target_col].apply(lambda x: classify_returns(x, TARGET_THRESHOLD, FLIP))
        else:
            print(target_col, "not found")

    df = df.dropna()


    y_columns = df.columns[df.columns.str.startswith("target")]
    x_columns = df.columns[~df.columns.str.startswith("target")]
    X, Y = df.loc[:, x_columns].values, df.loc[:, y_columns].values

    print("Clean Data: Done!")

    return df, X, Y, x_columns, y_columns

def scale_x(X, start_index, end_index, scale_method = "standard"):
    if scale_method == "standard":
        scaler = sklearn.preprocessing.StandardScaler()
    elif scale_method == "minmax":
        scaler = sklearn.preprocessing.MinMaxScaler(feature_range = (0,1))

    train_x_data = X[start_index[0]:(end_index[0]+1)]
    scaler.fit(train_x_data)

    X = scaler.transform(X)

    print("Scaling: Done!")

    return X, scaler

def TSGenerator0(X, Y, SEQ_LEN, BATCH_SIZE, start_index, end_index):
    #Create TimeseriesGenerator
    train_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=True,
                                   start_index=start_index[0], end_index=end_index[0])
    # val_data_gen = TimeseriesGenerator(X, Y,
    #                                length=SEQ_LEN, sampling_rate=1,
    #                                batch_size=BATCH_SIZE,
    #                                shuffle=False,
    #                                start_index=start_index[1], end_index=end_index[1])
    val_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=False,
                                   start_index=start_index[2], end_index=end_index[2])

    shape_x = train_data_gen[0][0].shape
    shape_y = train_data_gen[0][1].shape
    print(shape_x, shape_y)
    print("Number of batches per epoch:", len(train_data_gen))
    print("TSGenerator: Done!")

    return train_data_gen, val_data_gen, shape_x, shape_y
