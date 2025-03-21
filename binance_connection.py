#!/usr/bin/env python3
"""
Handles connection and communication with Binance Testnet API
"""

import hmac
import time
import hashlib
import requests
import logging
from urllib.parse import urlencode

class BinanceConnection:
    """Connection handler for Binance Testnet API"""
    
    def __init__(self, api_key, api_secret, testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(__name__)
        
        # Use testnet endpoints
        if testnet:
            self.base_url = 'https://testnet.binance.vision/api'
        else:
            self.base_url = 'https://api.binance.com/api'
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = self._make_request('GET', '/v3/ping')
            self.logger.info("Successfully connected to Binance API")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance API: {e}")
            raise
    
    def get_server_time(self):
        """Get Binance server time"""
        response = self._make_request('GET', '/v3/time')
        return response['serverTime']
    
    def get_account_balance(self):
        """Get account balance"""
        response = self._make_request('GET', '/v3/account', {}, True)
        balances = {}
        for asset in response['balances']:
            if float(asset['free']) > 0 or float(asset['locked']) > 0:
                balances[asset['asset']] = {
                    'free': float(asset['free']),
                    'locked': float(asset['locked']),
                    'total': float(asset['free']) + float(asset['locked'])
                }
        return balances
    
    def get_symbol_info(self, symbol):
        """Get trading information for a symbol"""
        response = self._make_request('GET', '/v3/exchangeInfo')
        for s in response['symbols']:
            if s['symbol'] == symbol:
                return s
        return None
    
    def get_klines(self, symbol, interval, limit=500):
        """Get candlestick data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/v3/klines', params)
    
    def get_recent_trades(self, symbol, limit=500):
        """Get recent trades"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/v3/trades', params)
    
    def get_order_book(self, symbol, limit=100):
        """Get order book"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/v3/depth', params)
    
    def place_order(self, symbol, side, order_type, quantity, price=None, time_in_force='GTC'):
        """Place a new order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timestamp': int(time.time() * 1000)
        }
        
        if price:
            params['price'] = price
            
        if order_type == 'LIMIT':
            params['timeInForce'] = time_in_force
        
        return self._make_request('POST', '/v3/order', params, True)
    
    def cancel_order(self, symbol, order_id):
        """Cancel an order"""
        params = {
            'symbol': symbol,
            'orderId': order_id,
            'timestamp': int(time.time() * 1000)
        }
        return self._make_request('DELETE', '/v3/order', params, True)
    
    def get_open_orders(self, symbol=None):
        """Get all open orders"""
        params = {'timestamp': int(time.time() * 1000)}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/v3/openOrders', params, True)
    
    def execute_trade(self, signal):
        """Execute a trade based on a signal"""
        try:
            symbol = signal['symbol']
            side = signal['side']
            quantity = signal['quantity']
            order_type = signal.get('order_type', 'MARKET')
            price = signal.get('price', None)
            
            # Place the order
            order = self.place_order(symbol, side, order_type, quantity, price)
            
            # Set stop loss and take profit if applicable
            if 'stop_loss' in signal and order['status'] == 'FILLED':
                self.place_order(
                    symbol=symbol,
                    side='SELL' if side == 'BUY' else 'BUY',
                    order_type='STOP_LOSS_LIMIT',
                    quantity=quantity,
                    price=signal['stop_loss'],
                    time_in_force='GTC'
                )
            
            if 'take_profit' in signal and order['status'] == 'FILLED':
                self.place_order(
                    symbol=symbol,
                    side='SELL' if side == 'BUY' else 'BUY',
                    order_type='LIMIT',
                    quantity=quantity,
                    price=signal['take_profit'],
                    time_in_force='GTC'
                )
                
            return order
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return None
    
    def _sign_request(self, params):
        """Sign request with API secret"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return query_string + f"&signature={signature}"
    
    def _make_request(self, method, endpoint, params=None, signed=False):
        """Make HTTP request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query = self._sign_request(params)
            url = f"{url}?{query}"
            response = requests.request(method, url, headers=headers)
        else:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            else:
                response = requests.request(method, url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
