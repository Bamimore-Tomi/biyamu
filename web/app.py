import os,base64,io
from io import BufferedReader
from datetime import datetime
import time

from flask import Flask,request,Response
import telegram
import pymongo
import qrcode
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
client = pymongo.MongoClient(os.getenv('DB_URL'))
db = client[os.getenv('DB_NAME')]

def record_payment(id_,ref,email,amount,valid_from,valid_to):
    if db.students.find_one({"payments": {"$elemMatch": {"reference":ref}}}) is None:
        student = db.students.find_one({'id':id_})
        if len(student['payments'])>0:
            last_payment = student['payments'][-1]
            if last_payment['valid_to'] > valid_from:
                valid_from = last_payment['valid_to']
                valid_to = valid_from + 2678400
        db.students.update_one({'id':id_},{'$addToSet':{'payments':{'reference':ref,'email':email,'amount':amount,
        'valid_from':valid_from,'valid_to':valid_to}}})
        student = db.students.find_one({'id':id_})
        registered_courses = student['registered_courses']
        bot = telegram.Bot(token=os.getenv('TOKEN'))
        for i in registered_courses:
            text = i.split('|')
            bot.send_message(chat_id=student['chat_id'],text=f'Please Join {text[0]} with the link\n{text[-1]}')
        bot.send_message(chat_id=student['chat_id'],text='Please note that you will be removed from the group after 31 days')
        img = qrcode.make(f"Username:{student['username']}\nPayment Reference:{ref}\nExpiry Data:{datetime.fromtimestamp(valid_to).isoformat()}\nCourses:{','.join([i.split('|')[0] for i in registered_courses])}")
        imgByteArr = io.BytesIO()
        img.save(imgByteArr,format=img.format)
        imgByteArr = imgByteArr.getvalue()
        open('le.png','wb').write(imgByteArr)
        bot.send_photo(chat_id=student['chat_id'],photo=open('le.png','rb'))
    else:
        print('already RECORDED')
#2678400

@app.route('/')
def home():
    return 'Hello, World!'
@app.route('/payment/webhook/',methods=['POST'])
def payment_webhook():
    print(request.json)
    if request.json.get('event')=='charge.success':
        ref = request.json.get('data')['reference']
        amount = request.json.get('data')['amount']/100
        email = request.json.get('data').get('customer')['email']
        id_ = ref.split('_')[0]
        valid_from = time.time()
        valid_to = valid_from + 2678400
        record_payment(id_,ref,email,amount,valid_from,valid_to)
        return Response(status=200)
    return 200

if __name__ == "__main__":
    app.run(debug=True)