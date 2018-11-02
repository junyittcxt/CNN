import os
import pandas as pd
import time
import json
from dateutil import parser


def load_param_json(json_path):
    output_file = open(json_path).read()
    output_json = json.loads(output_file)
    return output_json

def days_hours_minutes(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60

def get_meta_from_data(raw_data_file):
    df = pd.read_csv(raw_data_file, nrows=200)

    td = pd.to_datetime(df.iloc[0:100,0]).diff().mode()[0]
    timeframe = days_hours_minutes(td)
    tf_list = [str(j) for j in timeframe]
    timeframe_code =  "D" + tf_list[0] + "H" + tf_list[1] + "M" + tf_list[2]

    df.set_index("Date", inplace = True)
    possible_assets = df.columns.values

    return timeframe_code, possible_assets

def parse_raw_param(p):
    DATA_PARAMS = p["DATA_PARAMS"]
    MODEL_PARAMS = p["MODEL_PARAMS"]
    num_instances = p["num_instances"]

    DATA_PARAMS["raw_data_file"] = os.path.join(DATA_PARAMS["raw_data_folder"], DATA_PARAMS["raw_data_file_name"])
    DATA_PARAMS["end_split"] = [parser.parse(j) for j in DATA_PARAMS["raw_date_split"]]
    timeframe_code, possible_assets = get_meta_from_data(DATA_PARAMS["raw_data_file"])
    DATA_PARAMS["possible_assets"] = possible_assets
    DATA_PARAMS["TimeFrame"] = timeframe_code

    trade_direction = DATA_PARAMS["trade_direction"]
    if trade_direction == "Long":
        DATA_PARAMS["FLIP"] = False
    elif trade_direction == "Short":
        DATA_PARAMS["FLIP"] = True
    else:
        DATA_PARAMS["FLIP"] = False if DATA_PARAMS["TARGET_THRESHOLD"] > 0 else True

    trade_direction_short = "S" if DATA_PARAMS["FLIP"] else "B"
    MODEL_PARAMS["training_code"] = MODEL_PARAMS["training_number"] + "_" + DATA_PARAMS["TimeFrame"] + "_" + trade_direction_short

    return DATA_PARAMS, MODEL_PARAMS, possible_assets, num_instances

def initialize_path_parameters(DATA_PARAMS, MODEL_PARAMS, TARGET_TO_PREDICT = None):
    if TARGET_TO_PREDICT is not None:
        DATA_PARAMS["TARGET_TO_PREDICT"] = TARGET_TO_PREDICT

    MODEL_PARAMS["INIT_TIME"] = str(int(time.time()))
    MODEL_PARAMS["ASSET_FOLDER_NAME"] = DATA_PARAMS["TARGET_TO_PREDICT"] + "_" + MODEL_PARAMS["INIT_TIME"]
    # MODEL_PARAMS["root_output_folder"] = "output"
    MODEL_PARAMS["outputmain_folder"] = os.path.join(MODEL_PARAMS["root_output_folder"], MODEL_PARAMS["training_code"], "ASSETS_MODELS")
    MODEL_PARAMS["collect_signal_folder"] = os.path.join(MODEL_PARAMS["root_output_folder"], MODEL_PARAMS["training_code"], "SIGNAL")
    MODEL_PARAMS["collect_bestmodel_folder"] = os.path.join(MODEL_PARAMS["root_output_folder"], MODEL_PARAMS["training_code"], "BESTMODEL")
    MODEL_PARAMS["project_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], MODEL_PARAMS["ASSET_FOLDER_NAME"])
    MODEL_PARAMS["models_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], MODEL_PARAMS["ASSET_FOLDER_NAME"], "models")
    MODEL_PARAMS["logs_folder"] = os.path.join(MODEL_PARAMS["outputmain_folder"], MODEL_PARAMS["ASSET_FOLDER_NAME"], "logs")

    return DATA_PARAMS, MODEL_PARAMS
