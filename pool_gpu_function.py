import os
import shutil
import glob
import time
import json
import pandas as pd
from multiprocessing import Pool
import multiprocessing as mp

from parse_json_param import *
from _v2_full_train_minute_price import *
import numpy as np

def delete_f(path, target_col, remove_folder = False, show_err = False):
    try:
        files_to_delete = [j for j in os.listdir(path) if target_col in j]
        for f in files_to_delete:
            if remove_folder:
                shutil.rmtree(os.path.join(path, f))
            else:
                os.remove(os.path.join(path, f))
            print("Removed:", os.path.join(path, f))
    except Exception as err:
            if show_err:
                print(err)


def run_process(param):
    DATA_PARAMS, MODEL_PARAMS, TARGET_TO_PREDICT = param
    try:
        DATA_PARAMS, MODEL_PARAMS = initialize_path_parameters(DATA_PARAMS, MODEL_PARAMS, TARGET_TO_PREDICT)
        target_col = DATA_PARAMS["TARGET_TO_PREDICT"]
        best_model_path =  MODEL_PARAMS["collect_bestmodel_folder"]
        best_signal_path =  MODEL_PARAMS["collect_signal_folder"]
        asset_model_path =  MODEL_PARAMS["outputmain_folder"]
        if os.path.exists(best_model_path) and os.path.exists(best_signal_path) and os.path.exists(asset_model_path):
            u1 = np.any([target_col in j for j in os.listdir(best_model_path)])
            u2 = np.any([target_col in j for j in os.listdir(best_signal_path)])
            if (u1 and u2):
                print("Skip:", target_col)
                return [1, TARGET_TO_PREDICT, "ok: continue", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            else:
                #"delete relevant model data"
                delete_f(path = best_model_path, target_col = target_col, remove_folder = False)
                delete_f(path = best_signal_path, target_col = target_col, remove_folder = False)
                delete_f(path = asset_model_path, target_col = target_col, remove_folder = True)
        else:
            main_setup_folder = os.path.join(MODEL_PARAMS["root_output_folder"], MODEL_PARAMS["training_code"])
            try:
                shutil.rmtree(main_setup_folder)
                print("Removed:", main_setup_folder)
            except Exception as err:
                print("Error removing:", main_setup_folder)
                print(err)

        full_train_minute_price(DATA_PARAMS, MODEL_PARAMS)
        return [1, TARGET_TO_PREDICT, "ok", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    except Exception as err:
        print("===================")
        print(err)
        print("===================")
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

    print("Setup Done,", json_setup_file, ". Time Elapsed:", (t1-t0)/3600, "hours.")


def run_by_gpu(json_files, gpu):
    for json_setup_file in json_files:
        device = load_param_json(json_setup_file)["MODEL_PARAMS"]["device"]
        if device == gpu:
            run_one_setup(json_setup_file)
