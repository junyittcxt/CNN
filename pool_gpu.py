import os
import glob
import time
import json
import pandas as pd
from multiprocessing import Pool
import multiprocessing as mp

from pool_gpu_function import *
from parse_json_param import *
from _full_train_minute_price import *
import numpy as np

def main():
    t_all = time.time()

    json_files = glob.glob(os.path.join("json_setup", "*.json"))
    json_and_device = dict()
    json_and_device["json"] = []
    json_and_device["device"] = []
    for json_setup_file in json_files:
        p = load_param_json(json_setup_file)
        json_and_device["json"].append(json_setup_file)
        json_and_device["device"].append(p["MODEL_PARAMS"]["device"])

    jobs = []
    for gpu in np.unique(json_and_device["device"]):
        p = mp.Process(target=run_by_gpu, args=(json_files,gpu))
        jobs.append(p)
        p.start()

    for proc in jobs:
        proc.join()

    t_all_2 = time.time()

print("Everything Done:", (t_all_2 - t_all)/3600, "hours")
print("Json files:", json_files)
print("Number of json:", len(json_files))

if __name__ == "__main__":
    main()
