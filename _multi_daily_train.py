from cnn_method import *
from cnn_preproc_function import *
from multi_cnn_preproc_function import *

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


optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-d", "--gpudevice", default="1", help="gpudevice")
opts = optparser.parse_args()[0]
assetindex = int(opts.assetindex)
gpudevice = opts.gpudevice

# assetindex = 0
# gpudevice = "1"

os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]=gpudevice
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

#36
possible_asset = ['EWZ', 'IWM', 'SPY', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'IYR',
       'XLV', 'OIH', 'EZU', 'XLB', 'EWT', 'XLY', 'EWH', 'EWW', 'DIA', 'EWY',
       'IBB', 'EWC', 'USDJPY', 'GBPUSD', 'USDCHF', 'USDCAD', 'EURGBP',
       'XAGUSD', 'XAUUSD', 'EURUSD', 'EWJ', 'SMH', 'EWG', 'AUDUSD', 'EURJPY',
       'NZDUSD']


if assetindex > len(possible_asset):
    raise Exception("assetindex > len")



print("=============================")
print(possible_asset[assetindex])
print("=============================")
DATA_PARAMS = dict()
DATA_PARAMS["raw_data_file"] = "./DATA/82_ETF_FOREX_1_DAY.csv"
DATA_PARAMS["end_split"] = [datetime.datetime(2011,1,1), datetime.datetime(2013,1,1), datetime.datetime(2015,1,1), datetime.datetime(2018,1,1)]
DATA_PARAMS["TARGET_TO_PREDICT"] = "Multi"
DATA_PARAMS["SELECTED_COLS"] = ["SPY", "EWZ", "SMH", "IBB", "EURUSD", "AUDUSD", "GBPUSD"]
DATA_PARAMS["FUTURE_PERIOD_PREDICT"] = 5
DATA_PARAMS["TARGET_FUNCTION"] = "cumulative_returns"
DATA_PARAMS["SEQ_LEN"] = 60
DATA_PARAMS["TARGET_THRESHOLD"] = 0.001
DATA_PARAMS["FLIP"] = False

MODEL_PARAMS = dict()
MODEL_PARAMS["BATCH_SIZE"] = 64
MODEL_PARAMS["EPOCHS"] = 500
MODEL_PARAMS["PATIENCE"] = 500
# MODEL_PARAMS["LEARNING_RATE"] = 0.005
MODEL_PARAMS["LEARNING_RATE"] = 0.0001
MODEL_PARAMS["monitor_loss"] = "val_loss"
MODEL_PARAMS["mode_loss"] = "min"
INIT_TIME =  str(int(time.time()))
MODEL_PARAMS["outputmain_folder"] = os.path.join("output", "RNN_Multi_1_long_60_5_day")
MODEL_PARAMS["project_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME)
MODEL_PARAMS["models_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME, "models")
MODEL_PARAMS["logs_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME, "logs")

print("Initialize Parameters: Done!")

locals().update(DATA_PARAMS)
locals().update(MODEL_PARAMS)

df = load_data_daily_close_missing(raw_data_file)
#Create target
df, X, Y, x_columns, y_columns = multi_create_target(df, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION, TARGET_THRESHOLD, FLIP, selected_cols = SELECTED_COLS)
#Split df and get index
start_index, end_index = get_index_from_date(df, end_split)
#Scale
X, scaler = scale_x(X, start_index, end_index, scale_method = "standard")
#TSGenerator
train_data_gen, val_data_gen, shape_x, shape_y = TSGenerator0(X, Y, SEQ_LEN, BATCH_SIZE, start_index, end_index)


init_dir(models_folder)
init_dir(logs_folder)
print("Initialize directories: Done!")

save_var(DATA_PARAMS, MODEL_PARAMS, scaler, project_folder)

t0 = time.time()

model = multi_rnn_model_conf_1(shape_x, shape_y)
adm = keras.optimizers.Adam(lr=LEARNING_RATE, beta_1=0.9, beta_2=0.999, epsilon=None, amsgrad=False, decay = 1e-6)
model.compile(optimizer=adm, loss='categorical_crossentropy', metrics=['accuracy'])

tensorboard = keras.callbacks.TensorBoard(log_dir=logs_folder)
filepath = "CNN-{epoch:03d}-{val_loss:.4f}-{val_acc:.4f}"
checkpoint = keras.callbacks.ModelCheckpoint("{}/{}.model".format(models_folder, filepath),
                                                   monitor=monitor_loss,
                                                   verbose=1,
                                                   save_best_only=False,
                                                   save_weights_only=False,
                                                   mode=mode_loss)
earlystopping = keras.callbacks.EarlyStopping(monitor=monitor_loss,
                                              mode=mode_loss,
                                              min_delta=0,
                                              patience=PATIENCE,
                                              verbose=1)
history = model.fit_generator(generator=train_data_gen,
                              validation_data=val_data_gen,
                              epochs=EPOCHS,
                              callbacks=[tensorboard, checkpoint, earlystopping],
                              verbose=1)

t1 = time.time()
print("Training Done:", t1-t0)
