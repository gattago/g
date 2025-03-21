#!/usr/bin/env python3
"""
Base Strategy class that all strategies inherit from
"""
import logging

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, config):
        self.config = config
        self.name = "base"
        self.logger = logging.getLogger(f"strategy.{self.name}")
        self.connection = None
        self.risk_manager = None
    
    def generate_signals(self, data):
        """
        Generate trading signals based on strategy rules
        
        Args:
            data: DataFrame with market data and indicators
            
        Returns:
            list: List of signal dictionaries
        """
        # This method should be overridden by subclasses
        return []
    
    def calculate_position_size(self, price, side):
        """
        Calculate position size based on risk parameters
        
        Args:
            price (float): Current price
            side (str): 'BUY' or 'SELL'
            
        Returns:
            float: Position size
        """
        # Basic position sizing - should be improved in production
        account_balance = self.get_account_balance()
        risk_amount = account_balance * self.config.RISK_PER_TRADE
        
        # Simple position sizing based on fixed risk percentage
        position_size = risk_amount / price
        
        # Make sure we don't exceed maximum position size
        position_size = min(position_size, self.config.MAX_POSITION_SIZE)
        
        # Round to appropriate decimal places based on symbol
        position_size = round(position_size, 6)  # Adjust decimal places as needed
        
        return position_size
    
    def get_account_balance(self):
        """Get account balance for position sizing"""
        if self.connection:
            # Get the quote currency (e.g., USDT in BTCUSDT)
            quote_currency = self.config.SYMBOL[-4:]
            balances = self.connection.get_account_balance()
            if quote_currency in balances:
                return balances[quote_currency]['free']
        
        # Default fallback value
        return 10000
