import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import optparse
import time
import json
from query_api import *

from multiprocessing import Pool
import multiprocessing as mp

# [os.system('python3 {} -s {} -k {} -p {} &'.format(py, strat, key, port)) for py, strat, key, port in zzip]

def run_api(strat, key, port, gpu, py = "api_single.py"):
    os.system('python3 {} -s {} -k {} -p {} -g {}'.format(py, strat, key, port, gpu))

def main(strat, portstart, gpu, skip = 0, max = None):
    try:
        #Get Strategy Meta from Google Sheet instead of json
        scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name('/media/workstation/Storage/GoogleProject/DeepLearningAlphaC.txt', scope)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open("TASK")
        worksheet_list = spreadsheet.worksheets()
        Accepted = spreadsheet.worksheet("Accepted").get_all_records()
        adf = pd.DataFrame(Accepted)
        adf = adf.astype("str")

        #Select a strat, and get strategy_meta from TASK.Accepted sheet
        strategy_meta = adf.loc[adf.Strategy == strat].to_dict(orient = "records")[0]
        # json_path = os.path.join("STRATEGY_META", "{}.json".format(strat))
        # output_file = open(json_path).read()
        # strategy_meta = json.loads(output_file)
        print("Doing Strategy: {}, Code: {}, Asset_B: {}, Asset_S: {}".format(strategy_meta["Strategy"],strategy_meta["Code"],strategy_meta["Asset_B"],strategy_meta["Asset_S"]))
    except Exception as err:
        print("Error at:", "Load strategy_meta")
        print(err)

    PATH_DICT = get_path_dict(strategy_meta)
    all_keys = []
    for k1, v1 in PATH_DICT.items():
        for k2,v2 in v1.items():
            all_keys.append("{}_{}".format(k1, k2))

    strats = [strat]*len(all_keys)
    keys = all_keys
    ports = np.arange(len(all_keys)) + portstart

    if max is None:
        max = 1000

    jobs = []
    #need testing on counter, and counter_skip
    counter = 0
    counter_skip = 0
    for strat, key, port in zip(strats, keys, ports):
        if counter_skip >= skip:
            if counter < max:
                p = mp.Process(target=run_api, args=(strat,key,port,gpu))
                jobs.append(p)
                p.start()
                time.sleep(10)
                counter = counter + 1
        counter_skip = counter_skip + 1

    print("===================")
    #Write keys and ports
    print("keys:", keys)
    print("ports:", ports[0], "to", ports[-1])
    # key_df = pd.DataFrame(dict(key = keys, port = ports))
    # key_df.to_csv(os.path.join("STRATEGY_KEYS_PORTS", "{}_{}_{}.csv".format(strat, ports[0], ports[-1])))
    print("===================")

    for proc in jobs:
        proc.join()

if __name__ == "__main__":
    optparser = optparse.OptionParser()
    optparser.add_option("-s", "--strat", default="1202", help="strat")
    optparser.add_option("-p", "--portstart", default="5100", help="strat")
    optparser.add_option("-g", "--gpu", default="0", help="strat")
    opts = optparser.parse_args()[0]
    strat = str(opts.strat)
    portstart = int(opts.portstart)
    gpu = str(opts.gpu)

    main(strat, portstart, gpu)
