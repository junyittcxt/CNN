import os
import glob
import time
import json
import numpy as np
import pandas as pd
from multiprocessing import Pool
import multiprocessing as mp

from pool_gpu_function import *
from parse_json_param import *
from _v2_full_train_minute_price import *

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main(task_df, max_gpu):
    t_all = time.time()

    jobs = []
    for gpu in range(max_gpu):
        gpu = str(gpu)
        sub_task_df = task_df[task_df["device"] == int(gpu)]
        if len(sub_task_df) > 0:
            p = mp.Process(target=run_by_gpu_2, args=(sub_task_df,gpu))
            jobs.append(p)
            p.start()

    for proc in jobs:
        proc.join()

    t_all_2 = time.time()

    print("Everything Done:", (t_all_2 - t_all)/3600, "hours")
    print("Setup(s) completed:", task_df["Code"])
    print("Number of json:", len(task_df))

if __name__ == "__main__":
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    
    optparser = optparse.OptionParser()
    optparser.add_option("-s", "--sheetname", default="Z_5_DLTask", help="sheet")
    optparser.add_option("-g", "--maxgpu", default="2", help="max_gpu")
    optparser.add_option("-p", "--pcname", default="0", help="pcname")
    opts = optparser.parse_args()[0]

    sheet_name = str(opts.sheetname)
    max_gpu = int(opts.maxgpu)
    pc_name = int(opts.pcname)

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('./Credential/DeepLearningAlphaC.txt', scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open("TASK")

    # worksheet_list = spreadsheet.worksheets()
    worksheet = spreadsheet.worksheet(sheet_name)

    column_list = worksheet.range('A1:R1')
    task_df = pd.DataFrame(worksheet.get_all_records(), columns=[cell.value for cell in column_list])
    task_df["row"] = np.arange(len(task_df)) + 2
    task_df = task_df[task_df["Training"] == ""]

    if pc_name == 3:
        task_df = task_df[task_df["PC"] == "THR-WS"]
    elif pc_name == 4:
        task_df = task_df[task_df["PC"] == "FOU-WS"]
    elif pc_name == 5:
        task_df = task_df[task_df["PC"] == "FIV-WS"]

    if len(task_df) == 0:
        print(sheetname, ": Nothing to run!")
    else:
        main(task_df, max_gpu)
