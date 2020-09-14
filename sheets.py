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
    vip = client.open(sheet_name).worksheet('players').col_values(1)
    super_vip = client.open(sheet_name).worksheet('players').col_values(9)

    players = vip
    players.extend(super_vip)

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
        client.open(sheet_name).worksheet(worksheet).append_row(data,value_input_option='USER_ENTERED')
        return "Added to gsheet\n"
    except:
        error = sys.exc_info()[0]
        return str(error)


def find_player(user_id, worksheet='players'):
    client = gspread.authorize(creds)
    cells = client.open(sheet_name).worksheet(worksheet).findall(user_id)
    return cells

def update_player_bonus_date(user_id, date_time,  worksheet='players'):
    try:
        client = gspread.authorize(creds)
        wsheet = client.open(sheet_name).worksheet(worksheet)
        cells = find_player(user_id)

        for cell in cells:
            row_number = cell.row
            col_number = cell.col + 1

            wsheet.update_cell(row_number,col_number , date_time)

            # retrieve value from comment field, append 'Auto updated' string and update comment
            comment = wsheet.cell(row_number, col_number + 1).value
            if not comment.strip():
                comment = "Auto updated"
            else: 
                comment +="\nAuto updated"
            
            wsheet.update_cell(row_number,col_number + 1 , comment)
        
        return f"{len(cells)} bonus date updated\n"
    
    except:
        error = sys.exc_info()[0]
        return str(error)
