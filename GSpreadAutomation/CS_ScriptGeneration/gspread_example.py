import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd


scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('/media/workstation/Storage/GoogleProject/DeepLearningAlphaC.txt', scope)

gc = gspread.authorize(credentials)

spreadsheet = gc.open("TASK")

worksheet_list = spreadsheet.worksheets()
Z_M5_Sheet = spreadsheet.worksheet("Z_5_DLTask")

print(worksheet_list)

M5_dict = Z_M5_Sheet.get_all_records()
df = pd.DataFrame(M5_dict)
print(df)


#
# print(rec)
