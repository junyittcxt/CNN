import os
import glob
import time
import json
import pandas as pd
from multiprocessing import Pool
import multiprocessing as mp

from parse_json_param import *
from _full_train_minute_price import *
import numpy as np

def run_process(param):
    DATA_PARAMS, MODEL_PARAMS, TARGET_TO_PREDICT = param
    try:
        DATA_PARAMS, MODEL_PARAMS = initialize_path_parameters(DATA_PARAMS, MODEL_PARAMS, TARGET_TO_PREDICT)
        full_train_minute_price(DATA_PARAMS, MODEL_PARAMS)
        return [1, TARGET_TO_PREDICT, "ok", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    except Exception as err:
        return [0, TARGET_TO_PREDICT, err, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

def run_one_setup(json_setup_file):
    p = load_param_json(json_setup_file)
    DATA_PARAMS, MODEL_PARAMS, possible_assets, num_instances = parse_raw_param(p)
    runs_params = [(DATA_PARAMS, MODEL_PARAMS, TARGET_TO_PREDICT) for TARGET_TO_PREDICT in possible_assets]

    t0 = time.time()
    pool = Pool(processes=num_instances)
    run_status = pool.map(run_process, runs_params)
    pool.close()
    pool.join()

    #completion_df
    completion_df = pd.DataFrame(run_status, columns=["status","target","err", "completion_time"]).set_index("target")
    completion_df.to_csv(os.path.join("json_setup", "CompletionSummary", os.path.basename(json_setup_file).split(".")[0] + ".csv"))

    #move parameter to done
    shutil.move(json_setup_file, os.path.join("json_setup", "Done"))

    t1 = time.time()

    print("Setup Done,", json_setup_file, ". Time Elapsed:", t1-t0, "seconds.")


def run_by_gpu(json_files, gpu):
    for json_setup_file in json_files:
        device = load_param_json(json_setup_file)["MODEL_PARAMS"]["device"]
        if device == gpu:
            run_one_setup(json_setup_file)
