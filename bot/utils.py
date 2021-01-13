import string
import random

from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction


def payment_url(unique_id:str,email:str,amount:int):
    paystack = Paystack(secret_key='sk_test_9732b12c6b35b8e39013cdfcc3bdf4a9ec95ab9d')
    random_ = ''.join(random.choice(string.ascii_letters) for i in range(5))
    reference = f'{unique_id}_{random_}'
    response = Transaction.initialize(reference=reference,email=email,amount=amount)
    if response.get('status')==True:
        url = response['data']['authorization_url']
        reference  = response['data']['reference']
    return url, reference

if __name__=='__main__':
    url, refrence = payment_url('asdfasdf','tomibami2020@gmail.com',500)
    print(url, refrence)