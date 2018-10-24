import optparse
import pandas as pd
import numpy as np
from sklearn import preprocessing
import tensorflow as tf
import os, time, sys, sklearn
from sklearn.externals import joblib
from rnn_functions import *
import time
from keras.models import Sequential
from keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D
import keras
import os
from sklearn.utils import class_weight
from performance_function import *

os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]="0"
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)


optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-l", "--lossmethod", default=0, help="lossmethod")
optparser.add_option("-t", "--testindex", default=0, help="testindex")
opts = optparser.parse_args()[0]
assetindex=int(opts.assetindex)
loss_method=int(opts.lossmethod)
test_index=int(opts.testindex)

possible_asset = ['AUDUSD', 'EURUSD', 'EURGBP', 'EURJPY', 'EWH', 'EWZ', 'FXI', 'IAU', 'EZU', 'KRE', 'LQD', 'NZDUSD', 'EEM', 'EFA',
 'GDX', 'HYG', 'SPY', 'XLU', 'IYR', 'GLD', 'EWT', 'IEF', 'AGG', 'UNG', 'USDJPY', 'GBPUSD', 'USDCAD', 'SLV', 'RSX', 'EWJ', 'OIH',
 'SMH', 'XLB', 'TLT', 'USDCHF', 'USO', 'XLF', 'XLK', 'XLP', 'XOP', 'VEA', 'VWO', 'XLE', 'XLI', 'XLV', 'XRT', 'XLY', 'VNQ', 'EWW', 'XBI']

DATA_PARAMS = dict()
DATA_PARAMS["TARGET_TO_PREDICT"] = possible_asset[assetindex] #CHANGE THIS ONLY

DATA_PARAMS["FUTURE_PERIOD_PREDICT"] = 5
DATA_PARAMS["SEQ_LEN"] = 60
DATA_PARAMS["TARGET_THRESHOLD"] = 0.001


data_dir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "data")
test_data_dir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "data", "test")
if loss_method == 0:
    models_folder = assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "models_loss")
else:
    models_folder = assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "models_precision")

#pick best models
files = [f for f in os.listdir(models_folder) if os.path.isfile(os.path.join(models_folder,f))]
max_index = np.argmax([int(f.split("-")[1]) for f in files])
best_model_file = files[max_index]
best_model_path = os.path.join(models_folder,best_model_file)
model = tf.keras.models.load_model(best_model_path,
            custom_objects=None,
            compile=False
        )
#load dataset
if test_index == 0:
    test_t = joblib.load(os.path.join(test_data_dir,"test_t.pkl"))
    test_y = joblib.load(os.path.join(test_data_dir,"test_y.pkl"))
    test_x = joblib.load(os.path.join(test_data_dir,"test_x.pkl"))

else:
    test_t = joblib.load(os.path.join(test_data_dir,"test2_t.pkl"))
    test_y = joblib.load(os.path.join(test_data_dir,"test2_y.pkl"))
    test_x = joblib.load(os.path.join(test_data_dir,"test2_x.pkl"))

test_x, _ = reshape2(test_x)
#predict (inference)
raw_pred_y = model.predict(test_x)
y_pred = np.array(raw_pred_y).flatten()

#performance
perf(test_y, y_pred, t = 0.5)

#output signal_df
signal_df = pd.DataFrame(dict(Date = test_t, raw_signal = y_pred))

output_signal_dir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "signal")
init_dir(output_signal_dir)
signal_filename = "m{loss_method}_{test_index}_test_signal.csv".format(loss_method=loss_method, test_index=test_index)
signal_df.set_index("Date").to_csv(os.path.join(output_signal_dir, signal_filename))

if test_index == 1:
    output_signal_dir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "signal")
    signal0_filename = "m{loss_method}_{test_index}_test_signal.csv".format(loss_method=loss_method, test_index=0)
    signal1_filename = "m{loss_method}_{test_index}_test_signal.csv".format(loss_method=loss_method, test_index=1)
    df_list = [pd.read_csv(os.path.join(output_signal_dir, j)) for j in [signal0_filename, signal1_filename]]
    full_signal_df=pd.concat(df_list).set_index("Date")
    full_signal_df.to_csv(os.path.join(output_signal_dir, "m{loss_method}_full_test_signal.csv".format(loss_method=loss_method)))
