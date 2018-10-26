import numpy as np
import pandas as pd
import os

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

# def reshape2(x):
#     s = [j for j in x.shape]
#     x2 = x.reshape(s[0],s[1],s[2],1)
#
#     return x2, s

def filter_off_trading_day(df, target, threshold = 0.1):
    df["hh"] = df.index.hour
    df["mm"] = df.index.minute
    df["ss"] = df.index.second
    df["wkday"] = df.index.weekday
    df = df.groupby(["hh", "mm", "ss", "wkday"]).filter(lambda x: np.mean(x[target]!=0) > threshold)
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
