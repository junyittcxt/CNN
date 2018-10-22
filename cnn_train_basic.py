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
os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]="0"
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-l", "--lossmethod", default=0, help="lossmethod")
opts = optparser.parse_args()[0]
assetindex = int(opts.assetindex)
loss_method = opts.lossmethod
possible_asset = ['AUDUSD', 'EURUSD', 'EURGBP', 'EURJPY', 'EWH', 'EWZ', 'FXI', 'IAU', 'EZU', 'KRE', 'LQD', 'NZDUSD', 'EEM', 'EFA',
 'GDX', 'HYG', 'SPY', 'XLU', 'IYR', 'GLD', 'EWT', 'IEF', 'AGG', 'UNG', 'USDJPY', 'GBPUSD', 'USDCAD', 'SLV', 'RSX', 'EWJ', 'OIH',
 'SMH', 'XLB', 'TLT', 'USDCHF', 'USO', 'XLF', 'XLK', 'XLP', 'XOP', 'VEA', 'VWO', 'XLE', 'XLI', 'XLV', 'XRT', 'XLY', 'VNQ', 'EWW', 'XBI']

DATA_PARAMS = dict()
DATA_PARAMS["TARGET_TO_PREDICT"] = possible_asset[assetindex] #CHANGE THIS ONLY

DATA_PARAMS["FUTURE_PERIOD_PREDICT"] = 5
DATA_PARAMS["SEQ_LEN"] = 60
DATA_PARAMS["TARGET_THRESHOLD"] = 0.001

dirdata = os.path.join('cnn',DATA_PARAMS["TARGET_TO_PREDICT"])
init_dir(dirdata)

assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "data")
# files = os.listdir(assetdir)
files = [f for f in os.listdir(assetdir) if os.path.isfile(os.path.join(assetdir,f))]
vars_name = [j.split(".")[0] for j in files]

j = 0
for j in range(len(vars_name)):
    exec(vars_name[j] + ' = joblib.load(os.path.join(assetdir, "' + vars_name[j] + '.pkl"))' )

EPOCHS = 200
if loss_method == "0":
    logs_folder = assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "logs_loss")
    models_folder = assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "models_loss")
else:
    logs_folder = assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "logs_precision")
    models_folder = assetdir = os.path.join("cnn", DATA_PARAMS["TARGET_TO_PREDICT"], "models_precision")
init_dir(logs_folder)
init_dir(models_folder)
class_weights = class_weight.compute_class_weight('balanced',
                                                 np.unique(train_y),
                                                 train_y)

t0 = time.time()

model = Sequential()
model.add(Conv2D(128, kernel_size=(15,1), activation='relu', input_shape=(train_x_shape[1],train_x_shape[2],1)))
model.add(Conv2D(16, kernel_size=(2,1), activation='relu'))
model.add(Flatten())
model.add(Dense(1, activation='sigmoid'))

adm = keras.optimizers.Adam(lr=0.0005, beta_1=0.9, beta_2=0.999, epsilon=None, amsgrad=False, decay = 1e-6)
model.compile(optimizer=adm, loss='binary_crossentropy', metrics=['accuracy', precision])

tensorboard = TensorBoard(log_dir=logs_folder)
filepath = "CNN-{epoch:03d}-{val_loss:.4f}-{val_acc:.4f}"
if loss_method == "0":
    monitor_loss = "val_loss"
    mode_loss = "min"
else:
    monitor_loss = "val_precision"
    mode_loss = "max"
checkpoint = tf.keras.callbacks.ModelCheckpoint("{}/{}.model".format(models_folder, filepath),
                                                   monitor=monitor_loss,
                                                   verbose=1,
                                                   save_best_only=False,
                                                   save_weights_only=False,
                                                   mode=mode_loss)
earlystopping = tf.keras.callbacks.EarlyStopping(monitor=monitor_loss, min_delta=0, patience=int(EPOCHS/3), verbose=0, mode=mode_loss)

history = model.fit(train_x, train_y, batch_size=256, validation_data=(val_x, val_y), epochs=EPOCHS, class_weight=class_weights, callbacks=[tensorboard, checkpoint, earlystopping])

t1 = time.time()
print(t1-t0)
