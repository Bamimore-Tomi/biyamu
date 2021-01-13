import os
import time
import json
from tqdm import tqdm

from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser,InputPeerEmpty

from telethon.tl.functions.messages import AddChatUserRequest, GetDialogsRequest, DeleteChatUserRequest

from dotenv import load_dotenv
import pymongo

load_dotenv()

groups = json.load(open('config.json'))['groups']
db = pymongo.MongoClient(os.getenv('DB_URL'))[os.getenv('DB_NAME')]
client = TelegramClient('tomibami', os.getenv('API_ID'), os.getenv('API_HASH')).start()

all_dialogue = client(GetDialogsRequest(offset_date=None,offset_id = 0,
    offset_peer=InputPeerEmpty(),limit = 1000,hash=0 ))

def main(group_id:int):
    #print(all_dialogue.chats[4].id)
    group = [i for i in all_dialogue.chats if i.id==group_id][0]

    all_students = [i['chat_id'] for i in db.students.find({}) if i['payments'][-1]['valid_to'] > time.time()]
    all_participants = client.get_participants(group, aggressive=True)
    admins = [i for i in all_participants if client.get_permissions(group,i).is_admin]
    to_remove = [i for i in all_participants if i.id not in all_students and i not in admins]
    for i in to_remove:
        client(DeleteChatUserRequest(chat_id=group.id,user_id=i))
if __name__=='__main__':
    while True:
        print("RUNNING LOOP")
        for i in groups:
            main(i[1])
        time.sleep(600)