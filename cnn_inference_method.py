from cnn_method import *
from cnn_preproc_function import *
from cnn_inference_method import *

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

from sklearn.externals import joblib

def model_inference(main_folder, setup_folder_name, loss_criteria, loss_mode, batch_size = 64):
    #SETUP INIT
    setup_path = os.path.join(main_folder, setup_folder_name)
    DATA_PARAMS = joblib.load(os.path.join(setup_path, "DATA_PARAMS.pkl"))
    MODEL_PARAMS = joblib.load(os.path.join(setup_path, "MODEL_PARAMS.pkl"))
    scaler = joblib.load(os.path.join(setup_path, "scaler.pkl"))

    globals().update(DATA_PARAMS)
    globals().update(MODEL_PARAMS)
    # locals().update(DATA_PARAMS)
    # locals().update(MODEL_PARAMS)

    print(DATA_PARAMS)
    print(MODEL_PARAMS)

    df = load_data(raw_data_file)
    df = clean_and_create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION, TARGET_THRESHOLD, FLIP)
    df, timestamp, all_data_gen = FullTSGenerator(df, scaler, batch_size, SEQ_LEN, old = True)

    #pick best model
    models_folder = os.path.join(setup_path, "models")
    files = [f for f in os.listdir(models_folder) if os.path.isfile(os.path.join(models_folder,f))]
    metric_dict = dict()
    metrics_1 = ["index", "loss", "accuracy", "precision", "f1"]
    for j,v in enumerate(metrics_1):
        try:
            metric_dict[v] = [int(f.split("-")[j+1]) for f in files]
        except:
            metric_dict[v] = [np.nan for f in files]

    if loss_mode == "max":
        best_index = np.argmax(metric_dict[loss_criteria])
    else:
        best_index = np.argmin(metric_dict[loss_criteria])

    best_model_file = files[best_index]
    best_model_path = os.path.join(models_folder,best_model_file)
    model = keras.models.load_model(best_model_path, custom_objects=None, compile=False)
    print("Best Model: Done!")

    t0 = time.time()
    y = model.predict_generator(all_data_gen)
    t1 = time.time()
    print("Prediction: Done!", t1-t0, "seconds!")

    signal_df = pd.DataFrame(dict(Date = timestamp, raw_signal = y.flatten())).set_index("Date")
    signal_file = "signal_" + TARGET_TO_PREDICT + "_" + loss_mode + "_" + loss_criteria + "_" + str(FLIP) + ".csv"
    signal_df.to_csv(os.path.join(setup_path, signal_file))

    print("Signal Output: Done!")
