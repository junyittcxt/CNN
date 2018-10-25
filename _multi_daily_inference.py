from cnn_method import *
from cnn_preproc_function import *
from multi_cnn_preproc_function import *
from inference_function import *
from performance_function import *

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
import shutil

from sklearn.externals import joblib

#OPTS PARSER
optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-d", "--gpudevice", default="1", help="gpudevice")
opts = optparser.parse_args()[0]

assetindex = int(opts.assetindex)
gpudevice = opts.gpudevice
# assetindex = 0
# gpudevice = "1"

#GPU CONFIG
os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]=gpudevice
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

####################
#SETUP INIT
####################
output_folder = "/home/workstation/Desktop/CNN/output
setup_folder = "RNN_Multi_1_long_60_5_day"
main_folder = os.path.join(output_folder, setup_folder)
collect_signal_folder =  os.path.join(output_folder, "signal_" + setup_folder)
daily = True
batch_size = 64

####################
#END OF SETUP INIT
####################
init_dir(collect_signal_folder)

try:
    setups_folder = [j for j in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder,j))]
    print(setups_folder)
    setup_folder_name = setups_folder[assetindex]
    print("Running:", setup_folder_name)

except Exception as err:
    print("Index:", assetindex, "--SETUP ERROR!")
    raise Exception(err)

setup_path = os.path.join(main_folder, setup_folder_name)
DATA_PARAMS = joblib.load(os.path.join(setup_path, "DATA_PARAMS.pkl"))
MODEL_PARAMS = joblib.load(os.path.join(setup_path, "MODEL_PARAMS.pkl"))
scaler = joblib.load(os.path.join(setup_path, "scaler.pkl"))
locals().update(DATA_PARAMS)
locals().update(MODEL_PARAMS)

if daily:
    df = load_data_daily_close_missing(raw_data_file)
    #Create target
    df, X, Y, x_columns, y_columns = multi_create_target(df, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION, TARGET_THRESHOLD, FLIP, selected_cols = SELECTED_COLS)
    X = scaler.transform(X)

    all_data_gen = TimeseriesGenerator(X, Y,
                       length=SEQ_LEN, sampling_rate=1,
                       batch_size=BATCH_SIZE,
                       shuffle=False)
    timestamp = df.index.values
    shape_x = all_data_gen[0][0].shape
    shape_y = all_data_gen[0][1].shape
    print(shape_x, shape_y, X.shape, Y.shape, len(timestamp))
    print("Number of batches per epoch:", len(all_data_gen))
    print("TSGenerator: Done!")


#Pick best model
models_folder = os.path.join(setup_path, "models")
mdf = parse_model_folder(models_folder)
fmdf, best_model_file = best_model_score_multi(mdf)
best_model_path = os.path.join(models_folder,best_model_file)
model = keras.models.load_model(best_model_path, custom_objects=None, compile=False)
print("Best Model: Done!")

#Prediction
t0 = time.time()
y = model.predict_generator(all_data_gen)
t1 = time.time()
print("Prediction: Done!", t1-t0, "seconds!")

#Remove existing signal file
try:
    os.remove(glob.glob(os.path.join(main_folder, setup_folder_name, "*.csv"))[0])
except:
    print("Error deleting signal.csv:", setup_folder_name)

#Signal Output
lower = len(timestamp)-y.shape[0]
Date = timestamp[lower:]
signal_df = pd.DataFrame(y, index = Date, columns = y_columns)
signal_file = "signal_" + setup_folder_name + "_" + str(FLIP) + ".csv"
signal_df.to_csv(os.path.join(setup_path, signal_file))
print("Signal Output: Done!")

shutil.copy2(best_model_path, setup_path)
print("Copy best model: Done!")

signal_df.to_csv(os.path.join(collect_signal_folder, signal_file))
print("Collect signal.csv: Done!")

#Scoring
actual_df = pd.DataFrame(Y[lower:], index = Date, columns = y_columns)
L = np.sum(signal_df.index <= DATA_PARAMS["end_split"][0])
for i in range(y.shape[1]):
    yscore = signal_df.values[L:,i]
    ytrue = actual_df.values[L:,i]
    perf(ytrue,yscore, t = 0.5)
    print("===============", i)
    print("===============", i)
