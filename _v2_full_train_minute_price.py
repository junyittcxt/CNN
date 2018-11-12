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

# optparser = optparse.OptionParser()
# optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
# optparser.add_option("-d", "--gpudevice", default="0", help="gpudevice")
# opts = optparser.parse_args()[0]
#
# assetindex = int(opts.assetindex)
# gpudevice = opts.gpudevice

def full_train_minute_price(DATA_PARAMS, MODEL_PARAMS):
    gpudevice = str(MODEL_PARAMS["device"])
    os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
    os.environ["CUDA_VISIBLE_DEVICES"]=gpudevice
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    session = tf.Session(config=config)

    globals().update(DATA_PARAMS)
    globals().update(MODEL_PARAMS)
    print(TARGET_TO_PREDICT)

    try:
        CLEAN_METHOD_X = DATA_PARAMS["CLEAN_METHOD_X"]
    except:
        print("CLEAN_METHOD_X default to breakout_only_x")
        CLEAN_METHOD_X = "breakout_only_x"

    print("====== PREPROCESSING =======")
    t0 = time.time()
    df = load_data(raw_data_file)
    df = clean_data_x(df, target_col = TARGET_TO_PREDICT, window = BREAKOUT_WINDOW, method = CLEAN_METHOD_X)
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
    signal_file = "signal_" + TARGET_TO_PREDICT + "_" + str(FLIP) + "_" + str(INIT_TIME) + ".csv"
    signal_df.to_csv(os.path.join(project_folder, signal_file))
    print("Prop:", np.mean(signal_df["signal_raw"] > 0.5))
    print("Signal Output: Done!")

    shutil.copy2(best_model_path, project_folder)
    print("Copy best model: Done!")

    shutil.copy2(best_model_path, os.path.join(collect_bestmodel_folder, TARGET_TO_PREDICT + "_" + best_model_file))
    print("Collect best model: Done!")

    signal_df.to_csv(os.path.join(collect_signal_folder, signal_file))
    print("Collect signal.csv: Done!")
