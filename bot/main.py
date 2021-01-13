import os
import logging
import json
import threading
import time
import random 
import string 

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters,ConversationHandler,CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
import pymongo

from keyboard import courses_keyboard, yes_or_no
from utils import payment_url

import pickle

load_dotenv()
#parse_mode=telegram.ParseMode.MARKDOWN
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.ERROR)
config = json.load(open("./config.json"))
TOKEN = os.getenv('TOKEN')
client = pymongo.MongoClient(os.getenv('DB_URL'))
db = client[os.getenv('DB_NAME')]

ENROLL, NEW_COURSE, PAYMENT_INITIATED, EMAIL_PROMPT = range(4)
def start(updater,context):
    chat_id = updater.effective_chat.id
    if db.students.find_one({'chat_id':chat_id})==None:
        id_ = ''.join(random.choice(string.ascii_letters) for i in range(7))
        first_name = updater.message.chat.first_name
        last_name = updater.message.chat.last_name
        username = updater.message.chat.username
        db.students.insert_one({'id':id_,'chat_id':chat_id,'first_name':first_name,'last_name':last_name,'username':username,
        'payments':[],'registered_courses':[]})
    context.bot.send_message(chat_id=chat_id,text=config['messages']['introduction'])
def enroll(updater, context):
    chat_id = updater.effective_chat.id
    context.user_data['registered_courses']=[]
    context.bot.send_message(chat_id=chat_id,text=config['messages']['enroll'],reply_markup=courses_keyboard())
    context.bot.send_message(chat_id=chat_id,text=config['messages']['payment_prompt'])
    return ENROLL
def register_enrollment(updater,context):
    chat_id = updater.effective_chat.id
    query_data = updater.callback_query.data
    context.bot.send_message(chat_id=chat_id,text="Selected a new course {}".format(query_data.split('|')[0]))
    if query_data not in context.user_data['registered_courses']:
        context.user_data['registered_courses'].append(query_data)
    else:
        context.bot.send_message(chat_id=chat_id, text=config['messages']['course_selected_error'])
        context.bot.send_message(chat_id=chat_id,text=config['messages']['payment_prompt'])
    return -1
def payment(updater,context):
    chat_id = updater.effective_chat.id
    context.user_data['id'] = db.students.find_one({'chat_id':chat_id}).get('id')
    db.students.update_one({'id':context.user_data['id']},{'$set':{'registered_courses':context.user_data['registered_courses']}})
    text = ' , '.join(i.split('|')[0] for i in context.user_data['registered_courses'])
    context.bot.send_message(chat_id=chat_id,text=config['messages']['course_list'].format(text))
    if context.user_data.get('user_email') is None:
        context.bot.send_message(chat_id=chat_id,text=config['messages']['email_prompt'])
        return EMAIL_PROMPT
    else:
        url,ref = payment_url(context.user_data['id'],context.user_data['user_email'],500000)
        context.bot.send_message(chat_id=chat_id,text=config['messages']['payment_url_response'].format(url),
        parse_mode=telegram.ParseMode.MARKDOWN)
        return -1
def payment_after_email(updater,context):
    chat_id = updater.effective_chat.id
    email = updater.message.text.strip()
    match_ = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if match_!=None:
        context.user_data['user_email']=email
        url, ref = payment_url(context.user_data['id'],context.user_data['user_email'],500000)
        context.bot.send_message(chat_id=chat_id,text=config['messages']['payment_url_response'].format(url),
        parse_mode=telegram.ParseMode.MARKDOWN)
        return -1
    else:
        context.bot.send_message(chat_id=chat_id,text=config['messages']['email_prompt'])
        return EMAIL_PROMPT


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    entry = CommandHandler('start',start)

    enroll_conv = ConversationHandler(
        entry_points = [CommandHandler('enroll', enroll),CallbackQueryHandler(register_enrollment)],
        states= {
            ENROLL : [CallbackQueryHandler(register_enrollment)]
        },
        allow_reentry = True,
        fallbacks= [CommandHandler('enroll',enroll)]
    )
    pay_conv = ConversationHandler(
        entry_points = [CommandHandler('payNow',payment)],
        states = {
            EMAIL_PROMPT: [MessageHandler(Filters.regex(r'@'),payment_after_email)]
        },
        fallbacks= [CommandHandler('enroll',enroll)]
        )

    dispatcher.add_handler(entry)
    dispatcher.add_handler(enroll_conv)
    dispatcher.add_handler(pay_conv)

    updater.start_polling()
    updater.idle()

if __name__=='__main__':
    main()
