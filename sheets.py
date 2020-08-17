import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os 
from datetime import datetime
import sys



scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

cred_file_name = os.environ.get("CRED_FILE")
sheet_name = os.environ.get("SHEET_NAME")

creds = ServiceAccountCredentials.from_json_keyfile_name(cred_file_name, scope)

def in_player_list(player_id):
    client = gspread.authorize(creds)
    players = client.open(sheet_name).worksheet('players').col_values(1)

    if player_id in players:
        return True
    else: 
        return False 
    
def get_withdrawal_threashold():
    client = gspread.authorize(creds)
    withdrawal_threashold = client.open(sheet_name).worksheet('settings').cell(2, 1).value
    return int(withdrawal_threashold)

def insert_to_gsheet(data, worksheet):
    try:
        client = gspread.authorize(creds)
        client.open(sheet_name).worksheet(worksheet).append_row(data)
        return "Added to gsheet"
    except:
        error = sys.exc_info()[0]
        return str(error)


    