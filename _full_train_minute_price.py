#V2: Remove earlystopping, remove parameters: monitor_loss, loss_mode, patience
from cnn_method import *
from cnn_preproc_function import *
from inference_function import *

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

optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-d", "--gpudevice", default="0", help="gpudevice")
opts = optparser.parse_args()[0]

assetindex = int(opts.assetindex)
gpudevice = opts.gpudevice

os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]=gpudevice
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

#58
possible_asset = ['EURUSD', 'EEM', 'EFA', 'EWZ', 'FXI', 'GDX', 'HYG', 'IAU', 'IWM', 'SPY',
                   'USO', 'VWO', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'XOP', 'JNK',
                   'IYR', 'VEA', 'SLV', 'XLV', 'RSX', 'TLT', 'EWJ', 'OIH', 'GLD', 'EZU',
                   'KRE', 'SMH', 'XLB', 'XRT', 'LQD', 'EWT', 'XLY', 'VNQ', 'EWH', 'EWW',
                   'XBI', 'DIA', 'EWG', 'VGK', 'IEF', 'EMB', 'FEZ', 'AGG', 'ITB', 'EWC',
                   'UNG', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD',
                   'EURJPY', 'NZDUSD', 'XAGUSD']


if assetindex > len(possible_asset):
    raise Exception("assetindex > len")

print("=============================")
print(possible_asset[assetindex])
print("=============================")
DATA_PARAMS = dict()
DATA_PARAMS["raw_data_file"] = "./DATA/PRICE_LIQUIDASSET_60_MIN.csv"
DATA_PARAMS["end_split"] = [datetime.datetime(2011,1,1), datetime.datetime(2013,1,1), datetime.datetime(2017,1,1)]
DATA_PARAMS["TARGET_TO_PREDICT"] = possible_asset[assetindex]

DATA_PARAMS["BREAKOUT_WINDOW"] = 60
DATA_PARAMS["SEQ_LEN"] = 5
DATA_PARAMS["FUTURE_PERIOD_PREDICT"] = 1

DATA_PARAMS["TARGET_FUNCTION"] = "cumulative_returns"
DATA_PARAMS["TARGET_THRESHOLD"] = 0.001
DATA_PARAMS["FLIP"] = False if DATA_PARAMS["TARGET_THRESHOLD"] > 0 else True

MODEL_PARAMS = dict()
MODEL_PARAMS["keras_model_function"] = "rnn_model_conf_1_best"
MODEL_PARAMS["BATCH_SIZE"] = 256
MODEL_PARAMS["EPOCHS"] = 30
MODEL_PARAMS["LEARNING_RATE"] = 0.00005
INIT_TIME =  str(int(time.time()))
ASSET_FOLDER_NAME = DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME
MODEL_PARAMS["outputmain_folder"] = os.path.join("output", "R2M60p01_MODEL_RNN_3_Min_60_Breakout_Long_60_5_1")
MODEL_PARAMS["collect_signal_folder"] = os.path.join("output", "R2M60p01_SIGNAL")
MODEL_PARAMS["collect_bestmodel_folder"] = os.path.join("output", "R2M60p01_BESTMODEL")
MODEL_PARAMS["project_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], ASSET_FOLDER_NAME)
MODEL_PARAMS["models_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], ASSET_FOLDER_NAME, "models")
MODEL_PARAMS["logs_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], ASSET_FOLDER_NAME, "logs")

print("Initialize Parameters: Done!")

locals().update(DATA_PARAMS)
locals().update(MODEL_PARAMS)

print("====== PREPROCESSING =======")
t0 = time.time()
df = load_data(raw_data_file)
df = clean_data_breakout_x(df, target_col = TARGET_TO_PREDICT, breakout_window = BREAKOUT_WINDOW)
df = create_target_2(df, "target", FUTURE_PERIOD_PREDICT, TARGET_FUNCTION)
df = classify_target(df, "target", TARGET_THRESHOLD, FLIP)

df, X, Y, start_index, end_index, scaler = split_df(df, end_split, scale = True)
train_data_gen, val_data_gen, val_2_data_gen, test_data_gen, shape_x = TSGenerator(X, Y, SEQ_LEN, BATCH_SIZE, start_index, end_index)
class_weights = get_class_weights(df, start_index, end_index)

init_dir(models_folder)
init_dir(logs_folder)
print("Initialize directories: Done!")

save_var(DATA_PARAMS, MODEL_PARAMS, scaler, project_folder)
print("Save meta-data: Done!")
t1 = time.time()
print("PREPROCESSING Done:", t1-t0)

print("====== TRAINING =======")
t0 = time.time()
model, history = keras_training(keras_model_function, shape_x, LEARNING_RATE, logs_folder, models_folder, train_data_gen, val_data_gen, EPOCHS, class_weights)
t1 = time.time()
print("Training Done:", t1-t0)

print("====== INFERENCE =======")
init_dir(collect_signal_folder)
init_dir(collect_bestmodel_folder)
#INFERENCE, PRED SIGNAL
df, timestamp, all_data_gen = FullTSGeneratorDirect(df, X, Y, SEQ_LEN, batch_size = 64)

#Pick best model
mdf = parse_model_folder(models_folder)
fmdf, best_model_file = best_model_score(mdf)
best_model_path = os.path.join(models_folder, best_model_file)
model = keras.models.load_model(best_model_path, custom_objects=None, compile=False)
print("Best Model: Done! --", best_model_file)

#Prediction
t0 = time.time()
y = model.predict_generator(all_data_gen)
t1 = time.time()
print("Prediction: Done!", t1-t0, "seconds!")

#Signal Output
signal_df = pd.DataFrame(dict(Date = timestamp, signal_raw = y.flatten())).set_index("Date")
signal_file = "signal_" + TARGET_TO_PREDICT + "_" + str(FLIP) + ".csv"
signal_df.to_csv(os.path.join(project_folder, signal_file))
print("Prop:", np.mean(signal_df["signal_raw"] > 0.5))
print("Signal Output: Done!")

shutil.copy2(best_model_path, project_folder)
print("Copy best model: Done!")

shutil.copy2(best_model_path, os.path.join(collect_bestmodel_folder, TARGET_TO_PREDICT + "_" + best_model_file))
print("Collect best model: Done!")

signal_df.to_csv(os.path.join(collect_signal_folder, signal_file))
print("Collect signal.csv: Done!")
