import json,os
from telegram import InlineKeyboardButton,InlineKeyboardMarkup, KeyboardButton
import pymongo
from dotenv import load_dotenv

load_dotenv()

client = pymongo.MongoClient(os.getenv('DB_URL'))
db = client[os.getenv('DB_NAME')]
courses = db.config.find_one({})['config']['groups']

def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu

def courses_keyboard():
    courses_button = [InlineKeyboardButton(i[0], callback_data=f'{i[0]}|{i[1]}|{i[2]}') for i in courses]
    courses_menu = build_menu(courses_button,2)
    keyboard = InlineKeyboardMarkup(courses_menu)
    return keyboard
def yes_or_no():
    options = [('Yes',1),('No',0)]
    options_button = [InlineKeyboardButton(i[0],callback_data=i[1]) for i in options]
    options_menu = build_menu(options_button,2)
    keyboard = InlineKeyboardMarkup(options_menu)
    return keyboard
if __name__=='__main__':
    c = yes_or_no()
    print(c)