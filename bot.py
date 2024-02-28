import requests
import json
import time
import hashlib
import hmac
import os

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
        response = requests.get(url, headers=headers).json()
        bid, ask = response[0]['bidPrice'], response[0]['askPrice']
        return bid, ask
    
    def get_position(self):
        endpoint = f'position?filter=%7B%22symbol%22%3A%20%22{self.symbol}%22%7D'
        url = self.base_url + endpoint
        headers = self.generate_signature('GET', endpoint)
        response = requests.get(url, headers=headers).json()
        isOpen, quantity = response[0]['isOpen'], response[0]['currentQty']
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
        response = requests.post(url, headers=headers, data=data_json).json()
        return response
    
    def cancel_orders2(self):
        endpoint = 'order/cancelAllAfter'
        url = self.base_url + endpoint
        data = {
            'timeout': 1
        }
        data_json = json.dumps(data)
        headers = self.generate_signature('POST', endpoint, data_json)
        headers['Content-Type'] = 'application/json'
        response = requests.post(url, headers=headers, data=data_json).json()
        return response
    
    def cancel_orders(self, timeout):
        endpoint = f'order/cancelAllAfter?timeout={timeout*1000}'
        url = self.base_url + endpoint
        headers = self.generate_signature('POST', endpoint)
        response = requests.post(url, headers=headers).json()
        return response
    
class Bot():
    def __init__(self, _exchange):
        self.exchange = _exchange
        self.sleeping_time = 10
        self.last_bid = 0
        self.last_ask = 0
        
    def calculate_order(self):
        position, current_quantity = self.exchange.get_position()
        quantity = abs(current_quantity) + self.exchange.standard_quantity
        bid, ask = self.exchange.get_quote()
        if current_quantity >= 0 and self.last_ask != ask:
            self.exchange.place_order('Sell', quantity, ask)
            self.last_ask = ask
        if current_quantity <= 0 and self.last_bid != bid:
            self.exchange.place_order('Buy', quantity, bid)
            self.last_bid = bid

    def trade(self):
        while True:
            bid, ask = self.exchange.get_quote()
            if bid != self.last_bid or ask != self.last_ask:
                self.exchange.cancel_orders(self.sleeping_time-1)
            time.sleep(self.sleeping_time)
            self.calculate_order()
        
            

    
    
print()
bitmex = Exchange()
#print(bitmex.get_quote())
#print(bitmex.get_position())
#print(bitmex.place_order('Buy',1000,60000))
bot = Bot(bitmex)
#print(bot.calculate_order())
#bitmex.place_order('Sell', 1000, 60000)
#time.sleep(5)
#print(bitmex.cancel_orders(1))
bot.trade()