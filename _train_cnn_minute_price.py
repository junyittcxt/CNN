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
DATA_PARAMS["end_split"] = [datetime.datetime(2011,1,1), datetime.datetime(2013,1,1), datetime.datetime(2015,1,1), datetime.datetime(2018,1,1)]
DATA_PARAMS["TARGET_TO_PREDICT"] = possible_asset[assetindex]
DATA_PARAMS["FUTURE_PERIOD_PREDICT"] = 1
DATA_PARAMS["TARGET_FUNCTION"] = "cumulative_returns"
DATA_PARAMS["SEQ_LEN"] = 5
DATA_PARAMS["BREAKOUT_WINDOW"] = 60
DATA_PARAMS["TARGET_THRESHOLD"] = 0.001
DATA_PARAMS["FLIP"] = False

MODEL_PARAMS = dict()
MODEL_PARAMS["BATCH_SIZE"] = 256
MODEL_PARAMS["EPOCHS"] = 900
MODEL_PARAMS["PATIENCE"] = 900
MODEL_PARAMS["LEARNING_RATE"] = 0.00005
MODEL_PARAMS["monitor_loss"] = "val_loss"
MODEL_PARAMS["mode_loss"] = "min"
INIT_TIME =  str(int(time.time()))
MODEL_PARAMS["outputmain_folder"] = os.path.join("output", "R2M60p01_RNN_3_Min_60_Breakout_Long_5_1")
MODEL_PARAMS["project_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME)
MODEL_PARAMS["models_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME, "models")
MODEL_PARAMS["logs_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + INIT_TIME, "logs")

print("Initialize Parameters: Done!")

locals().update(DATA_PARAMS)
locals().update(MODEL_PARAMS)

df = load_data(raw_data_file)
df = clean_data_breakout_x(df, target_col = TARGET_TO_PREDICT, breakout_window = BREAKOUT_WINDOW)
df = create_target_2(df, "target", FUTURE_PERIOD_PREDICT, TARGET_FUNCTION)
df = classify_target(df, "target", TARGET_THRESHOLD, FLIP)

df, X, Y, start_index, end_index, scaler = split_df(df, end_split, scale = True)
train_data_gen, val_data_gen, test_1_data_gen, test_2_data_gen, shape_x = TSGenerator(X, Y, SEQ_LEN, BATCH_SIZE, start_index, end_index)
class_weights = get_class_weights(df, start_index, end_index)

init_dir(models_folder)
init_dir(logs_folder)
print("Initialize directories: Done!")

save_var(DATA_PARAMS, MODEL_PARAMS, scaler, project_folder)

t0 = time.time()

model = rnn_model_conf_1_best(shape_x)
# model = rnn_model_conf_1_best(shape_x)
adm = keras.optimizers.Adam(lr=LEARNING_RATE, beta_1=0.9, beta_2=0.999, epsilon=None, amsgrad=False, decay = 1e-6)
# f1 = F1Score()
model.compile(optimizer=adm, loss='binary_crossentropy', metrics=['accuracy', precision, f1])

tensorboard = keras.callbacks.TensorBoard(log_dir=logs_folder)
filepath = "RNN1-{epoch:03d}-{val_loss:.4f}-{val_acc:.4f}-{val_precision:.4f}-{val_f1:.4f}"
checkpoint = keras.callbacks.ModelCheckpoint("{}/{}.model".format(models_folder, filepath),
                                                   monitor=monitor_loss,
                                                   verbose=1,
                                                   save_best_only=False,
                                                   save_weights_only=False,
                                                   mode=mode_loss,
                                                   period=3)
earlystopping = keras.callbacks.EarlyStopping(monitor=monitor_loss,
                                              mode=mode_loss,
                                              min_delta=0,
                                              patience=PATIENCE,
                                              verbose=1)
history = model.fit_generator(generator=train_data_gen,
                              validation_data=val_data_gen,
                              epochs=EPOCHS,
                              class_weight=class_weights,
                              callbacks=[tensorboard, checkpoint, earlystopping],
                              verbose=1)

t1 = time.time()
print("Training Done:", t1-t0)


#INFERENCE, PRED SIGNAL
