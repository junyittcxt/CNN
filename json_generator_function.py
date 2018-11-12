import json


def gen_template():
    temp_dict = {
         "DATA_PARAMS":{
            "raw_data_folder": "DATA",
            "raw_data_file_name": "PRICE_LIQUIDASSET_15_MIN.csv",
            "raw_data_file": "1__need_parse/filepath",

            "raw_date_split": ["20110101", "20130101", "20170101"],
            "end_split": "2__need_parse/datetime",

            "possible_assets": "3a__need_parse",
            "TARGET_TO_PREDICT": "3__need_parse/SPY",
            "TimeFrame": "4__need_parse/D0H0M30",

            "BREAKOUT_WINDOW": 20,
            "SEQ_LEN": 10,
            "FUTURE_PERIOD_PREDICT": 3,
            "TARGET_FUNCTION": "cumulative_returns",
            "TARGET_THRESHOLD": 0.001,
            "trade_direction": "Auto/Long/Short",
            "FLIP": "4__need_parse/True/False"
         },
          "MODEL_PARAMS":   {
            "device": "0",
            "keras_model_function": "rnn_model_conf_1_best",
            "BATCH_SIZE": 256,
            "EPOCHS": 900,
            "LEARNING_RATE": 0.00005,
            "training_number": "C005",
            "training_code": "5__need_parse/C001_D0H0M30_B/C001_D0H0M30_S",
            "root_output_folder": "/media/workstation/Storage/DL_Output"
         },
         "num_instances": 5
        }
    return temp_dict


#def write_json():
