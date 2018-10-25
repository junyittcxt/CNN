import os
import numpy as np
import pandas as pd

def parse_model_folder(models_folder):
    files = [f for f in os.listdir(models_folder) if os.path.isfile(os.path.join(models_folder,f))]
    filenames = [f.split(".model")[0] for f in files]

    metric_dict = dict()
    metrics_1 = ["index", "loss", "accuracy", "precision", "f1"]
    for j,v in enumerate(metrics_1):
        try:
            vals = [float(f.split("-")[j+1]) for f in filenames]
            metric_dict[v] = vals
        except:
            metric_dict[v] = [np.nan for f in filenames]
    mdf = pd.DataFrame(metric_dict)
    mdf["files"] = files
    mdf["filenames"] = filenames
    return mdf

def inverse_percentile(arr, num):
    arr = sorted(arr)
    i_arr = [i for i, x in enumerate(arr) if x > num]

    return i_arr[0] / len(arr) if len(i_arr) > 0 else 1

def vect_inverse_percentile(arr):
    out = []
    for x in arr:
        out.append(inverse_percentile(arr, x))
    return out

def best_model_score(mdf):
    mdf2 = mdf.set_index("index").sort_index()
    mdf2["f1_2"] = vect_inverse_percentile(mdf2["f1"].values)
    mdf2["accuracy_2"] = vect_inverse_percentile(mdf2["accuracy"].values)
    mdf2["precision_2"] = vect_inverse_percentile(mdf2["precision"].values)
    mdf2["loss_2"] = vect_inverse_percentile(mdf2["loss"].values)

    mdf2["score"] = (mdf2["f1_2"] + mdf2["accuracy_2"] + 2*mdf2["precision_2"])/4 - mdf2["loss_2"]
    mdf2["chg_score_1"] = np.abs(mdf2["score"]-mdf2["score"].shift(1)) + 1e-6
    mdf2["chg_score_5"] = np.abs(mdf2["score"]-mdf2["score"].shift(5)) + 1e-6
    mdf2["chg_score_10"] = np.abs(mdf2["score"]-mdf2["score"].shift(10)) + 1e-6
    mdf2["chg_score_agg"] = np.power(mdf2["chg_score_1"]*mdf2["chg_score_5"]*mdf2["chg_score_10"],1/3)
    mdf2["final_score"] = mdf2["score"]/mdf2["chg_score_agg"]

    fmdf = mdf2.sort_values("final_score", ascending = False)
    best_file = fmdf["files"].values[0]
    return fmdf, best_file

def best_model_score_multi(mdf):
    mdf2 = mdf.set_index("index").sort_index()
    mdf2["accuracy_2"] = vect_inverse_percentile(mdf2["accuracy"].values)
    mdf2["loss_2"] = vect_inverse_percentile(mdf2["loss"].values)

    mdf2["score"] = mdf2["accuracy_2"] - mdf2["loss_2"]
    mdf2["chg_score_1"] = np.abs(mdf2["score"]-mdf2["score"].shift(1)) 
    mdf2["chg_score_5"] = np.abs(mdf2["score"]-mdf2["score"].shift(5))
    mdf2["chg_score_10"] = np.abs(mdf2["score"]-mdf2["score"].shift(10))
    mdf2["chg_score_agg"] = (mdf2["chg_score_1"]+mdf2["chg_score_5"]+mdf2["chg_score_10"])/3
    mdf2["final_score"] = mdf2["score"]/mdf2["chg_score_agg"]

    fmdf = mdf2.sort_values("final_score", ascending = False)
    best_file = fmdf["files"].values[0]
    return fmdf, best_file
