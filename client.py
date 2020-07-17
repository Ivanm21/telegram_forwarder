

from telethon import TelegramClient, events
import logging
import os 

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)



phone = os.environ.get('PHONE')
api_id = os.environ.get('APPID')
api_hash = os.environ.get('APIHASH')
client = TelegramClient('session_name', api_id, api_hash)

to_channel = os.environ.get('TO_CHANNEL')
from_channel = os.environ.get('FROM_CHANNEL')




@client.on(events.NewMessage(chats=from_channel, incoming=True))
async def forwarder(event):
    print(event.message.message)
    to_channel = os.environ.get('TO_CHANNEL')
    
    await client.send_message(entity=to_channel, message=event.message.message)
    print('Message sent')

print('Listening for messages...')

client.start(phone)

client.run_until_disconnected()

# async def main():
#         # Getting information about yourself
#     me = await client.get_me()

#     # "me" is an User object. You can pretty-print
#     # any Telegram object with the "stringify" method:
#     print(me.stringify())
#         # You can print all the dialogs/conversations that you are part of:
#     async for dialog in client.iter_dialogs():
#         print(dialog.name, 'has ID', dialog.id)


# with client:
#     client.loop.run_until_complete(main())    