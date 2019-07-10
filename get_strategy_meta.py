import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_all_strategy_meta(gsheet = "TASK", wsheet = "Accepted", credentials_path = None):
    if credentials_path is None:
        credentials_path = '/media/workstation/Storage/GoogleProject/DeepLearningAlphaC.txt'
        
    try:
        #Get Strategy Meta from Google Sheet instead of json
        scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open(gsheet)
        worksheet_list = spreadsheet.worksheets()
        Accepted = spreadsheet.worksheet(wsheet).get_all_records()
        adf = pd.DataFrame(Accepted)
        adf = adf.astype("str")

        #Select a strat, and get strategy_meta from TASK.Accepted sheet
        strategy_meta = adf
        return strategy_meta
    except Exception as err:
        print("Error at:", "get_all_strategy_meta")
        print(err)
        raise err
        
def get_strategy_meta(strat, credentials_path = None):
    if credentials_path is None:
        credentials_path = '/media/workstation/Storage/GoogleProject/DeepLearningAlphaC.txt'
        
    try:
        #Get Strategy Meta from Google Sheet instead of json
        scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open("TASK")
        worksheet_list = spreadsheet.worksheets()
        Accepted = spreadsheet.worksheet("Accepted").get_all_records()
        adf = pd.DataFrame(Accepted)
        adf = adf.astype("str")

        #Select a strat, and get strategy_meta from TASK.Accepted sheet
        strategy_meta = adf.loc[adf.Strategy == strat].to_dict(orient = "records")[0]
        print("Loaded Strategy Metadata: {}, Code: {}, Asset_B: {}, Asset_S: {}".format(strategy_meta["Strategy"],strategy_meta["Code"],strategy_meta["Asset_B"],strategy_meta["Asset_S"]))
        return strategy_meta
    except Exception as err:
        print("Error at:", "Load strategy_meta")
        print(err)
        raise err