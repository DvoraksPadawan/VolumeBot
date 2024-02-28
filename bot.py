import requests
import json
import time
import hashlib
import hmac
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

class Exchange():
    def __init__(self, testnet = True):
        if testnet:
            self.base_url = 'https://testnet.bitmex.com/api/v1/'
        else:
            self.base_url = 'https://www.bitmex.com/api/v1/'
        self.symbol = 'XBTUSDT'
        self.standard_quantity = 1000
    
    def generate_signature(self, method, endpoint, data = ''):
        url = '/api/v1/' + endpoint
        api_key = os.getenv("API_KEY")
        api_secret = os.getenv("SECRET_KEY")
        expires = int(round(time.time()) + 5)
        message = method + url + str(expires) + data
        signature = hmac.new(bytes(api_secret, 'utf-8'), bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
        return {
            'api-expires': str(expires),
            'api-key': api_key,
            'api-signature': signature
        }
    
    def get_quote(self):
        endpoint = f'quote?symbol={self.symbol}&count=1&reverse=true'
        url = self.base_url + endpoint
        headers = self.generate_signature('GET', endpoint)
        response = session.get(url, headers=headers).json()
        try:
            print("try quote")
            bid, ask = response[0]['bidPrice'], response[0]['askPrice']
        except KeyError as e:
            bid,ask = self.get_quote()
        return bid, ask
    
    def get_position(self):
        endpoint = f'position?filter=%7B%22symbol%22%3A%20%22{self.symbol}%22%7D'
        url = self.base_url + endpoint
        headers = self.generate_signature('GET', endpoint)
        response = session.get(url, headers=headers).json()
        try: 
            print("try position")
            isOpen, quantity = response[0]['isOpen'], response[0]['currentQty']
        except KeyError as e:
            isOpen, quantity = self.get_position()
        return isOpen, quantity
    
    def place_order(self, side, quantity, price):
        endpoint = 'order'
        url = self.base_url + endpoint
        data = {
            'symbol': self.symbol,
            'side': side,
            'orderQty': quantity,
            'price': price,
            'ordType': 'Limit',
            'execInst' : 'ParticipateDoNotInitiate'
        }
        data_json = json.dumps(data)
        headers = self.generate_signature('POST', endpoint, data_json)
        headers['Content-Type'] = 'application/json'
        response = session.post(url, headers=headers, data=data_json).json()
        return response
    
    def cancel_all_orders(self, timeout = 1):
        endpoint = f'order/cancelAllAfter?timeout={timeout}'
        url = self.base_url + endpoint
        headers = self.generate_signature('POST', endpoint)
        response = session.post(url, headers=headers).json()
        return response
    
    def delete_all_orders(self):
        endpoint = f'order/all'
        url = self.base_url + endpoint
        headers = self.generate_signature('DELETE', endpoint)
        response = session.delete(url, headers=headers).json()
        return response
    
    def get_orders(self):
        endpoint = f'order?count=2&reverse=true'
        url = self.base_url + endpoint
        headers = self.generate_signature('GET', endpoint)
        response = session.get(url, headers=headers).json()
        try: 
            print("try get orders")
            order1_id, order2_id = response[0]['orderID'], response[1]['orderID']
        except KeyError as e:
            order1_id, order2_id = self.get_orders()
        return order1_id, order2_id
    
    def delete_order(self, order_id):
        endpoint = f'order/{order_id}'
        url = self.base_url + endpoint
        print(url)
        headers = self.generate_signature('DELETE', endpoint)
        response = session.delete(url, headers=headers).json()
        return response

    
class Bot():
    def __init__(self, _exchange):
        self.exchange = _exchange
        self.sleeping_time = 10
        self.my_last_bid = 0
        self.my_last_ask = 0
        self.my_last_quantity = 0
        
    def calculate_order(self, current_quantity, bid, ask):
        quantity = abs(current_quantity) + self.exchange.standard_quantity
        if current_quantity >= 0:
            self.exchange.place_order('Sell', quantity, ask)
            self.my_last_ask = ask
        if current_quantity <= 0:
            self.exchange.place_order('Buy', quantity, bid)
            self.my_last_bid = bid

    def calculate_change(self):
        changed = False
        position, current_quantity = self.exchange.get_position()
        if current_quantity != self.my_last_quantity:
            changed = True
        self.my_last_quantity = current_quantity
        bid, ask = self.exchange.get_quote()
        if bid != self.my_last_bid and current_quantity <= 0:
            changed = True
        if ask != self.my_last_ask and current_quantity >= 0:
            changed = True
        if changed:
            self.exchange.delete_all_orders()
            #delete self.old orders
            #self.old orders =
            self.calculate_order(current_quantity, bid, ask)

    def trade(self):
        while True:
            time.sleep(self.sleeping_time)
            self.calculate_change()
        
            


bitmex = Exchange(False)
bot = Bot(bitmex)
#order1, order2 = bitmex.get_orders()
#print(bitmex.delete_order(order1))
bot.trade()