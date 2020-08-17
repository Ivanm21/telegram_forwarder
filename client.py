

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


phone = os.environ.get('PHONE')
api_id = os.environ.get('APPID')
api_hash = os.environ.get('APIHASH')
session_name = os.environ.get("SESSION_NAME")

client = TelegramClient(session_name, api_id, api_hash)

to_channel = os.environ.get('TO_CHANNEL')
from_channel = os.environ.get('FROM_CHANNEL')
withdrawals_channel = os.environ.get("WITHDRAWALS_CHANNEL")

pattern = re.compile(r'[↗️]+') 
pattern_deposit = re.compile(r'[↘️]+') 
withdrawal_success_string = "WITHDRAWAL SUCCESS"
deposits_worksheet = 'raw data'
withdrawal_worksheet = 'withdrawals raw'


@client.on(events.NewMessage(chats=from_channel, pattern=pattern_deposit))
async def forward_deposit(event):
    print(event.message.message)
    # to_channel = os.environ.get('TO_CHANNEL')
    # %B %d, %Y at %I:%M%p
    date_time = datetime.now().strftime("%B %d, %Y at %I:%M%p")
    message = event.message.message


    result = sheets.insert_to_gsheet([date_time, message], deposits_worksheet) 
    await client.send_message(entity=from_channel, message=result)
    print('Message inserted')

@client.on(events.NewMessage(chats=from_channel, pattern=pattern))
async def forward_withdrawals(event):
    print(event.message.message)
    message = event.message.message
    user_id = message.partition('User id:')[2].split('\n')[0].strip()
    header = message.partition("\n")[0]

    try:
        withdrawal_amount_with_currency =  message.lower().partition('amount:')[2].split('\n')[0].strip()
        withdrawal_amount = float(Decimal(sub(r'[^\d.]', '', withdrawal_amount_with_currency)))
        currency = withdrawal_amount_with_currency.split(" ")[1].strip().upper()
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

    in_list = sheets.in_player_list(user_id)
    withdrawal_threshold = sheets.get_withdrawal_threashold()
    
    print(f'User in user list - {in_list}')
    print(f'withdrawal threshold - {withdrawal_threshold}')
    print("====================\n")

    # Check if it is WITHDRAWAL SUCCESS
    if withdrawal_success_string in message:
        print("WITHDRAWAL SUCCESS")
        date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        result = sheets.insert_to_gsheet([date_time, user_id, withdrawal_amount_eur], withdrawal_worksheet) 


    if in_list or (withdrawal_amount_eur > withdrawal_threshold) or (exchange_rate == -1):
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
