import warnings

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

import sklearn
from sklearn import preprocessing
from sklearn.utils import class_weight

from cnn_preproc_function import *
import numpy as np
import pandas as pd

# from sklearn.externals import joblib
import joblib
import keras
from keras.preprocessing.sequence import TimeseriesGenerator

from keras_model_configuration import *
from keras_metric import *

def load_data(raw_data_file):
    #Load
    df = pd.read_csv(raw_data_file)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    print("Load Data: Done!")

    return df

def load_data_daily_close_missing(raw_data_file, missing_threshold = 0.1):
    #Load
    df = pd.read_csv(raw_data_file)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    missing_threshold = 0.1
    u1 = df.apply(lambda x: np.mean(np.isnan(x)) < missing_threshold)
    df2 = df.loc[:, u1]
    df2.fillna(method = "ffill").dropna()
    rdf = df2.pct_change().dropna()
    print("Load Data: Done!")

    return rdf

def clean_data_x(df, target_col, window, method = "breakout_only_x"):
    if method == "breakout_only_x":
        df = clean_data_breakout_x(df, target_col = target_col, breakout_window = window)
    if method == "prob_only_x":
        df = clean_data_prob_x(df, target_col = target_col, window = window)

    return df

    
def clean_data_breakout_x(df, target_col, breakout_window = 60):
    price_df = df.fillna(method = "ffill").dropna()
    return_df = df.pct_change()

    return_df = filter_off_trading_day(return_df, target_col)
    filtered_index = return_df.index
    price_df = price_df.reindex(filtered_index)
    x_df = price_df.rolling(window = breakout_window).apply(lambda x: breakout(x)*1,raw = False)
    return_df["target"] = return_df[target_col]
    fdf = pd.merge(x_df, return_df[["target"]], left_index = True, right_index = True)
    fdf.dropna()

    return fdf

def clean_data_prob_x(df, target_col, window):
    price_df = df.fillna(method = "ffill").dropna()
    return_df = df.pct_change()
    rdf2 = return_df.copy()

    return_df = filter_off_trading_day(return_df, target_col)
    x_df = rdf2.rolling(window = window).apply(lambda x: diff_probability(x)*1,raw = False)
    return_df["target"] = return_df[target_col]
    fdf = pd.merge(x_df, return_df[["target"]], left_index = True, right_index = True)

    return fdf


def clean_and_create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION, TARGET_THRESHOLD, FLIP, filter_tradingday = True):
    #Clean and Create Target
    if filter_tradingday:
        df = filter_off_trading_day(df, target = TARGET_TO_PREDICT, threshold = 0.1)

    if TARGET_FUNCTION == "cumulative_returns":
        TARGET_FUNCTION_R = cumulative_returns
    elif TARGET_FUNCTION == "mod_sharpe":
        TARGET_FUNCTION_R = mod_sharpe

    try:
        df = create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION_R)
    except:
        df = create_target(df, TARGET_TO_PREDICT, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION)
    df = classify_target(df, "target", TARGET_THRESHOLD, FLIP)
    print("Clean Data: Done!")

    return df

def split_df(df, end_split, scale = True):
    #Split df and get index
    start_index, end_index = get_index_from_date(df, end_split)
    target_col= "target"
    x_columns = [j for j in df.columns if j != target_col]

    #Scaling
    # scaler = sklearn.preprocessing.MinMaxScaler(feature_range = (0,1))
    scaler = sklearn.preprocessing.StandardScaler()
    #Fit train_x
    train_x_data = df[x_columns].iloc[start_index[0]:(end_index[0]+1)].values
    if scale:
        scaler.fit(train_x_data)
        #Scale all
        df.loc[:,x_columns] = scaler.transform(df[x_columns])
    X = df[x_columns].values
    Y = df[target_col].values

    return df, X, Y, start_index, end_index, scaler



def TSGenerator(X, Y, SEQ_LEN, BATCH_SIZE, start_index, end_index):
    #Create TimeseriesGenerator
    train_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=True,
                                   start_index=start_index[0], end_index=end_index[0])
    val_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=False,
                                   start_index=start_index[1], end_index=end_index[1])
    val_2_data_gen = TimeseriesGenerator(X, Y,
                                   length=SEQ_LEN, sampling_rate=1,
                                   batch_size=BATCH_SIZE,
                                   shuffle=False,
                                   start_index=start_index[2], end_index=end_index[2])
    test_data_gen = None
    # test_data_gen = TimeseriesGenerator(X, Y,
    #                                length=SEQ_LEN, sampling_rate=1,
    #                                batch_size=BATCH_SIZE,
    #                                shuffle=False,
    #                                start_index=start_index[3], end_index=end_index[3])
    shape_x = train_data_gen[0][0].shape
    print(shape_x)
    print("Number of batches per epoch:", len(train_data_gen))
    print("TSGenerator: Done!")

    return train_data_gen, val_data_gen, val_2_data_gen, test_data_gen, shape_x

def get_class_weights(df, start_index, end_index):
    #Calculate class_weights
    train_y = df["target"].iloc[start_index[0]:(end_index[0]+1)].values
    class_weights = class_weight.compute_class_weight('balanced',
                                                     np.unique(train_y),
                                                     train_y)
    print(class_weights)

    return class_weights

def save_var(DATA_PARAMS, MODEL_PARAMS, scaler, project_folder):
    joblib.dump(DATA_PARAMS, os.path.join(project_folder,'DATA_PARAMS.pkl'))
    joblib.dump(MODEL_PARAMS, os.path.join(project_folder,'MODEL_PARAMS.pkl'))
    joblib.dump(scaler, os.path.join(project_folder,'scaler.pkl'))
    print("Data Saved!")

def keras_training(keras_model_function, shape_x, LEARNING_RATE, logs_folder, models_folder, train_data_gen, val_data_gen, EPOCHS, class_weights):
    if keras_model_function == "rnn_model_conf_1_best":
        KERAS_FUN = rnn_model_conf_1_best

    model = KERAS_FUN(shape_x)
    adm = keras.optimizers.Adam(lr=LEARNING_RATE, beta_1=0.9, beta_2=0.999, epsilon=None, amsgrad=False, decay = 1e-6)
    model.compile(optimizer=adm, loss='binary_crossentropy', metrics=['accuracy', precision, f1])

    tensorboard = keras.callbacks.TensorBoard(log_dir=logs_folder)
    filepath = "DL-{epoch:04d}-{val_loss:.4f}-{val_acc:.4f}-{val_precision:.4f}-{val_f1:.4f}"
    checkpoint = keras.callbacks.ModelCheckpoint("{}/{}.model".format(models_folder, filepath),
                                                       monitor="val_loss",
                                                       verbose=0,
                                                       save_best_only=False,
                                                       save_weights_only=False,
                                                       mode="auto",
                                                       period=3)

    history = model.fit_generator(generator=train_data_gen,
                                  validation_data=val_data_gen,
                                  epochs=EPOCHS,
                                  class_weight=class_weights,
                                  callbacks=[tensorboard, checkpoint],
                                  verbose=0)
    return model, history



########################
#INFERENCE
########################
def FullTSGenerator(df, scaler, batch_size, SEQ_LEN, old = False):
    #Split df and get index
    target_col= "target"
    x_columns = [j for j in df.columns if j != target_col]

    #Scale all
    if not old:
        df.loc[:,x_columns] = scaler.transform(df[x_columns])

    X = df[x_columns].values
    Y = df[target_col].values

    all_data_gen = TimeseriesGenerator(X, Y, length=SEQ_LEN, batch_size=batch_size, shuffle=False)
    timestamp = df.index[SEQ_LEN:]
    return df, timestamp, all_data_gen


def FullTSGeneratorDirect(df, X, Y, SEQ_LEN, batch_size = 64):
    all_data_gen = TimeseriesGenerator(X, Y, length=SEQ_LEN, batch_size=batch_size, shuffle=False)
    timestamp = df.index[SEQ_LEN:]
    return df, timestamp, all_data_gen
