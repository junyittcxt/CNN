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

from sklearn.externals import joblib

#OPTS PARSER
optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-d", "--gpudevice", default="0", help="gpudevice")
opts = optparser.parse_args()[0]

assetindex = int(opts.assetindex)
gpudevice = opts.gpudevice

#GPU CONFIG
os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]=gpudevice
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

####################
#SETUP INIT
####################
output_folder =  "/home/workstation/Desktop/CNN/output/"
setup_folder = "R3M30q01_RNN_3_Min_30_Breakout_Short_90_10_1"

# output_folder =  "/media/workstation/9EB4ABE9B4ABC1DF/DL_Output/"
# setup_folder = "R2M60p01_RNN_3_Min_60_Breakout_Long_5_1"

main_folder = os.path.join(output_folder, setup_folder)
collect_signal_folder =  os.path.join(output_folder, "SIGNAL_" + setup_folder)
daily = False

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


df = load_data(raw_data_file)
df = clean_data_breakout_x(df, target_col = TARGET_TO_PREDICT, breakout_window = BREAKOUT_WINDOW)
df = create_target_2(df, "target", FUTURE_PERIOD_PREDICT, TARGET_FUNCTION)
df = classify_target(df, "target", TARGET_THRESHOLD, FLIP)

df, X, Y, start_index, end_index, scaler = split_df(df, end_split, scale = True)
df, timestamp, all_data_gen = FullTSGenerator(df, scaler, batch_size, SEQ_LEN, old = False)

#Pick best model
models_folder = os.path.join(setup_path, "models")
mdf = parse_model_folder(models_folder)
fmdf, best_model_file = best_model_score(mdf)
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
signal_df = pd.DataFrame(dict(Date = timestamp, signal_raw = y.flatten())).set_index("Date")
signal_file = "signal_" + TARGET_TO_PREDICT + "_" + str(FLIP) + ".csv"
signal_df.to_csv(os.path.join(setup_path, signal_file))
print("Prop:", np.mean(signal_df["signal_raw"] > 0.5))
print("Signal Output: Done!")

shutil.copy2(best_model_path, setup_path)
print("Copy best model: Done!")

signal_df.to_csv(os.path.join(collect_signal_folder, signal_file))
print("Collect signal.csv: Done!")

#PARAMS:
# main_folder = os.path.join("output","no_scale_models")
# main_folder = "Z:/ML Training Data/_CNN_Output/daily"
# main_folder = "/home/workstation/Desktop/test_output_daily"
# setups_folder = [j for j in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder,j))]
# print(setups_folder)
# setup_folder_name = setups_folder[assetindex]
# print(setup_folder_name)
#
#
# loss_criteria = "precision"
# loss_mode = "max"
# batch_size = 64
# daily = True
# model_inference(main_folder, setup_folder_name, loss_criteria, loss_mode, batch_size, daily)
