

from telethon import TelegramClient, events
import logging
import os 
import sheets
from re import sub
from decimal import Decimal
import re
import crypto_prices
import sys
from datetime import datetime



logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

sheet_name = sys.argv[1]
from_channel = sys.argv[2]


phone = os.environ.get('PHONE')
api_id = os.environ.get('APPID')
api_hash = os.environ.get('APIHASH')
session_name = os.environ.get("SESSION_NAME")

client = TelegramClient(session_name, api_id, api_hash)

to_channel = os.environ.get('TO_CHANNEL')
withdrawals_channel = os.environ.get("WITHDRAWALS_CHANNEL")

pattern = re.compile(r'[↗️]+') 
pattern_deposit = re.compile(r'[↘️]+') 
pattern_cashback = re.compile(r'[🏦]+')

cashback_string = "CASHBACK"
withdrawal_success_string = "WITHDRAWAL SUCCESS"


deposits_worksheet = 'raw data'
withdrawal_worksheet = 'withdrawals raw'
cashback_worksheet = 'cashback'


@client.on(events.NewMessage(chats=from_channel, pattern=pattern_deposit))
async def forward_deposit(event):
    print(event.message.message)

    date_time = datetime.now().strftime("%B %d, %Y at %I:%M%p")
    message = event.message.message


    result = sheets.insert_to_gsheet([date_time, message], deposits_worksheet,sheet_name=sheet_name) 
    await client.send_message(entity=from_channel, message=result)
    print('Message inserted')


@client.on(events.NewMessage(chats=from_channel, pattern=pattern_cashback))
async def forward_cashback(event):
    print(event.message.message)
    message = event.message.message

    if cashback_string in message:
        date_time = datetime.now().strftime("%B %d, %Y at %I:%M%p")
        user_id_full = message.partition('User id:')[2].split('\n')[0].strip()
        user_id = int(Decimal(sub(r'[^\d.]', '', user_id_full)))
        
        amount_with_currency =  message.lower().partition('amount:')[2].split('\n')[0].strip()
        amount = float(Decimal(sub(r'[^\d.]', '', amount_with_currency)))

        currency = amount_with_currency.split(" ")[1].strip().upper()
        if currency != 'EUR':
            exchange_rate = crypto_prices.get_price_in_eur(currency)
            amount = exchange_rate*amount

        # Insert cashback
        result = sheets.insert_to_gsheet([date_time, user_id, amount], cashback_worksheet,sheet_name=sheet_name)

        # Update bonus date 
        date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        result += sheets.update_player_bonus_date(user_id_full,date_time,sheet_name=sheet_name)

        await client.send_message(entity=from_channel, message=result)
        print('Cashback inserted')



@client.on(events.NewMessage(chats=from_channel, pattern=pattern))
async def forward_withdrawals(event):
    print(event.message.message)
    message = event.message.message
    user_id = message.partition('User id:')[2].split('\n')[0].strip()
    header = message.partition("\n")[0]

    try:
        withdrawal_amount_with_currency =  message.lower().partition('amount:')[2].split('\n')[0].strip()

        withdrawal_amount_with_currency = withdrawal_amount_with_currency.split(" ")
        exchange_rate = 1



        if len(withdrawal_amount_with_currency) > 2:
            withdrawal_amount = float(Decimal(sub(r'[^\d.]', '', withdrawal_amount_with_currency[2])))
            currency = 'EUR'
        else:
            currency = withdrawal_amount_with_currency[1].strip().upper()
            amount  = withdrawal_amount_with_currency[0].strip().upper()
            withdrawal_amount = float(Decimal(sub(r'[^\d.]', '', amount)))
            exchange_rate = crypto_prices.get_price_in_eur(currency)

        withdrawal_amount_eur = exchange_rate*withdrawal_amount


    except:
        error = sys.exc_info()[0]
        error_message = "**ERROR WHILE PARSING:**\n"
        error_message += str(error) 
        error_message += "\n====================\n"
        error_message += message
        await client.send_message(entity=withdrawals_channel, message=error_message, parse_mode='md')
        return

    user_email = message.partition('Email:')[2].split('\n')[0].strip()
    print("====================\n")
    print(f'User ID is - {user_id}')
    print(f'Email is - {user_email}')
    print(f'withdrawal amount - {withdrawal_amount}')

    in_list = sheets.in_player_list(user_id,sheet_name=sheet_name)
    withdrawal_threshold = sheets.get_withdrawal_threashold(sheet_name=sheet_name)
    
    print(f'User in user list - {in_list}')
    print(f'withdrawal threshold - {withdrawal_threshold}')
    print("====================\n")

    # Check if it is WITHDRAWAL SUCCESS
    if withdrawal_success_string in message:
        print("WITHDRAWAL SUCCESS")
        date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        result = sheets.insert_to_gsheet([date_time, user_id, withdrawal_amount_eur], withdrawal_worksheet,sheet_name=sheet_name) 
        print(result)
        return

    if in_list or (withdrawal_amount_eur > withdrawal_threshold):
        print('Message sent')
        message = header + "\n"
        message += f"====================\n"
        message += f"**User ID:** {user_id}\n"
        message += f"**Email:** {user_email}\n"
        message += f"**Amount:** {withdrawal_amount:.2f} {currency} "
        if (exchange_rate > 0) and (exchange_rate != 1):
            message += f"**({withdrawal_amount_eur:.2f} EUR)**\n"
        elif exchange_rate == -1:
            message += f"**(---)**\n"
        else:
            message += "\n"
            
        message += f"====================\n"
        if in_list:
            message += "PLAYER IN LIST\n"
        if (withdrawal_amount_eur > withdrawal_threshold):
            message += f"WITHDRAWAL > {withdrawal_threshold}\n"

        await client.send_message(entity=withdrawals_channel, message=message, parse_mode='md')
        

print('Listening for messages...')

client.start(phone)

client.run_until_disconnected()
