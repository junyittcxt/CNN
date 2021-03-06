import numpy as np
import pandas as pd
import os
import functools

def reduce_concat(x, sep=""):
    return functools.reduce(lambda x, y: str(x) + sep + str(y), x)

def paste(*lists, sep=" ", collapse=None):
    result = map(lambda x: reduce_concat(x, sep=sep), zip(*lists))
    if collapse is not None:
        return reduce_concat(result, sep=collapse)
    return list(result)

def add_time_column(df):
    df["hh"] = df.index.hour
    df["mm"] = df.index.minute
    df["ss"] = df.index.second
    df["wkday"] = df.index.weekday
    return df

def add_temp_time_group(df):
    df["temp_time"] = paste(df["hh"], df["mm"], df["ss"], df["wkday"], sep = ",")
    return df

def target_accepted_index(df, target):
    temp_df = pd.DataFrame()
    y = df[target].values
    z = paste(df["hh"], df["mm"], df["ss"], df["wkday"], sep = ",")
    temp_df["z"] = z
    temp_df["y"] = y
    temp_df = temp_df.dropna()
    h = temp_df.groupby("z").apply(lambda x: np.mean(x)!=0)
    accepted_index = h.loc[h["y"]].index

    return accepted_index

def filter_df_by_accepted_index(df, accepted_index):
    df = add_time_column(df)
    df = add_temp_time_group(df)
    subset = [j in accepted_index.values for j in df["temp_time"].values]
    df = df.loc[subset]
    df = df.drop(["hh", "mm", "ss", "wkday","temp_time"], axis = 1)

    return df



def init_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def cumulative_returns(returns):
    return np.prod(1+np.array(returns)) - 1

def mod_sharpe(returns):
    n = len(returns)
    r =  np.prod(1+np.array(returns))-1
    s = np.std(np.array(returns))
    ss = r/s
    if np.isnan(ss):
        ss = 0
    return ss

def diff_probability(returns):
    n = len(returns)
    r = np.array(returns)
    d = np.sum(r > 0) - np.sum(r < 0)

    return d/n

# def reshape2(x):
#     s = [j for j in x.shape]
#     x2 = x.reshape(s[0],s[1],s[2],1)
#
#     return x2, s

def breakout(p):
    p = np.array(p)
    if p[-1] > np.max(p[0:-1]):
        return 1
    elif p[-1] < np.min(p[0:-1]):
        return -1
    else:
        return 0

def filter_off_trading_day(df, target, threshold = 0.1):
    df["hh"] = df.index.hour
    df["mm"] = df.index.minute
    df["ss"] = df.index.second
    df["wkday"] = df.index.weekday
    df = df.groupby(["hh", "mm", "ss", "wkday"]).filter(lambda x: np.mean(x[target]!=0) > threshold)
    return df

def create_target_2(df, target_col, FUTURE_PERIOD_PREDICT, TARGET_FUNCTION = "cumulative_returns", keras_preproc = True):
    if TARGET_FUNCTION == "cumulative_returns":
        TARGET_FUNCTION_R = cumulative_returns
    elif TARGET_FUNCTION == "mod_sharpe":
        TARGET_FUNCTION_R = mod_sharpe
    elif TARGET_FUNCTION == "mod_prob":
        TARGET_FUNCTION_R = diff_probability

    df.loc[:,'target'] = df[target_col].rolling(window = FUTURE_PERIOD_PREDICT).apply(lambda x: TARGET_FUNCTION_R(x))
    df.loc[:,'target'] = df['target'].shift(-FUTURE_PERIOD_PREDICT+1)
    df = df.dropna()
    return df

def create_target(df, target_col, FUTURE_PERIOD_PREDICT, FUNC = cumulative_returns, keras_preproc = True):
    df.loc[:,'target'] = df[target_col].rolling(window = FUTURE_PERIOD_PREDICT).apply(lambda x: FUNC(x))
    if keras_preproc:
        df.loc[:,'target'] = df['target'].shift(-FUTURE_PERIOD_PREDICT+1)
    else:
        df.loc[:,'target'] = df['target'].shift(-FUTURE_PERIOD_PREDICT)

    df = df.dropna()
    return df

def classify_returns(returns, threshold = 0, flip = False):
    if flip:
        if returns < threshold:
            return 1
        else:
            return 0
    else:
        if returns > threshold:
            return 1
        else:
            return 0

def classify_target(df, target_col = "target", threshold = 0, flip = False):
    df[target_col] = df[target_col].apply(lambda x: classify_returns(x, threshold, flip))
    return df

#end_split = [datetime.datetime(2011,1,1), datetime.datetime(2012,1,1), datetime.datetime(2016,1,1), datetime.datetime(2018,1,1)]
def get_index_from_date(df, end_split):
    end_index = [np.sum(df.index <= d)-1 for d in end_split]
    start_index = pd.Series(end_index)
    start_index = [int(j) for j in (start_index.shift(1) + 1).fillna(0).values]
    return start_index, end_index

#end_split = [datetime.datetime(2011,1,1), datetime.datetime(2012,1,1), datetime.datetime(2016,1,1), datetime.datetime(2018,1,1)]
# def split_df_by_data_get_index(df, end_split):
#     for i,d in enumerate(end_split):
#         np.sum(df.index <= d)
#
#
#
# def split_df_by_data(df, end_split):
#     df_list = []
#     for i,d in enumerate(end_split):
#         if i== 0:
#             df2 = df[df.index <= d]
#             df_list.append(df2)
#         else:
#             df2 = df[(df.index <= d) & (df.index > end_split[i-1])]
#             df_list.append(df2)
#
#
#     startdates = [z.index[0] for z in df_list]
#     enddates = [z.index[-1] for z in df_list]
#     print(startdates)
#     print(enddates)
#     return df_list
