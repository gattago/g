#!/usr/bin/env python3
"""
Risk Manager - Handles position sizing and risk management
"""
import logging
import pandas as pd

class RiskManager:
    """
    Risk Manager - Controls risk parameters for trades
    """
    
    def __init__(self, connection, config):
        self.connection = connection
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Keep track of open positions
        self.open_positions = {}
        
        # Initialize with current account state
        self.update_account_state()
    
    def update_account_state(self):
        """Update local state with current account information"""
        try:
            # Get account balances
            self.balances = self.connection.get_account_balance()
            
            # Get open orders
            open_orders = self.connection.get_open_orders()
            self.open_orders = {order['orderId']: order for order in open_orders}
            
            # Calculate total exposure
            self.calculate_exposure()
            
        except Exception as e:
            self.logger.error(f"Error updating account state: {e}")
    
    def calculate_exposure(self):
        """Calculate current market exposure"""
        # This is a simplified calculation
        # In a real implementation, you would use actual position values
        self.total_exposure = 0.0
        try:
            # For each trading pair we're interested in
            for symbol in [self.config.SYMBOL]:  # Expand this list if trading multiple symbols
                # Get balance of base currency
                base_currency = symbol[:-4]  # E.g., "BTC" from "BTCUSDT"
                if base_currency in self.balances:
                    # Get current market price
                    # This is simplified - should use actual price data
                    price = 1.0  # Placeholder
                    self.total_exposure += self.balances[base_currency]['total'] * price
        except Exception as e:
            self.logger.error(f"Error calculating exposure: {e}")
    
    def validate_trade(self, signal):
        """
        Validate if a trade should be executed based on risk parameters
        Returns True if trade should be executed, False otherwise
        """
        # Update account state first
        self.update_account_state()
        
        symbol = signal['symbol']
        side = signal['side']
        quantity = signal['quantity']
        price = signal.get('price', 0)
        
        # Check if we have reached maximum number of open trades
        if len(self.open_positions) >= self.config.MAX_OPEN_TRADES:
            self.logger.warning("Maximum number of open trades reached")
            return False
        
        # Check if we're already in a position for this symbol
        if symbol in self.open_positions:
            current_position = self.open_positions[symbol]
            # Allow adding to position in same direction but not in opposite direction
            if (side == 'BUY' and current_position['side'] == 'SELL') or \
               (side == 'SELL' and current_position['side'] == 'BUY'):
                self.logger.warning(f"Already have position in opposite direction for {symbol}")
                return False
        
        # Validate position size
        max_position_size = self.calculate_max_position_size(symbol, price)
        if quantity > max_position_size:
            original_quantity = quantity
            quantity = max_position_size
            signal['quantity'] = quantity
            self.logger.warning(f"Reduced position size from {original_quantity} to {quantity} due to risk limits")
        
        # Ensure position size meets minimum requirements
        min_position_size = 0.00001  # Adjust based on exchange requirements
        if quantity < min_position_size:
            self.logger.warning(f"Position size {quantity} too small, minimum is {min_position_size}")
            return False
        
        # Add stop loss if configured and not present
        if self.config.USE_STOP_LOSS and 'stop_loss' not in signal:
            if side == 'BUY':
                signal['stop_loss'] = price * (1 - self.config.STOP_LOSS_PCT)
            else:
                signal['stop_loss'] = price * (1 + self.config.STOP_LOSS_PCT)
        
        # Add take profit if not present
        if 'take_profit' not in signal:
            if side == 'BUY':
                signal['take_profit'] = price * (1 + self.config.TAKE_PROFIT_PCT)
            else:
                signal['take_profit'] = price * (1 - self.config.TAKE_PROFIT_PCT)
        
        # Check if total exposure would exceed limits after this trade
        trade_value = quantity * price
        if self.total_exposure + trade_value > self.get_account_value() * 0.9:
            self.logger.warning("Total exposure would exceed limits")
            return False
        
        return True
    
    def calculate_max_position_size(self, symbol, price):
        """Calculate maximum position size based on risk parameters"""
        account_value = self.get_account_value()
        risk_amount = account_value * self.config.RISK_PER_TRADE
        
        # Maximum position based on risk per trade
        max_position_from_risk = risk_amount / price
        
        # Maximum position based on config setting
        max_position_from_config = self.config.MAX_POSITION_SIZE
        
        # Return the smaller of the two
        return min(max_position_from_risk, max_position_from_config)
    
    def get_account_value(self):
        """Get total account value in quote currency (e.g., USDT)"""
        # Simplified implementation
        # In a real bot, you would convert all assets to quote currency value
        quote_currency = self.config.SYMBOL[-4:]  # e.g., "USDT" from "BTCUSDT"
        if quote_currency in self.balances:
            return self.balances[quote_currency]['total']
        return 10000  # Default fallback value
    
    def adjust_stops(self, open_trades):
        """Adjust trailing stops for open trades"""
        if not self.config.USE_TRAILING_STOP:
            return
            
        for trade_id, trade in open_trades.items():
            try:
                symbol = trade['symbol']
                side = trade['side']
                entry_price = trade['price']
                current_price = self.get_current_price(symbol)
                
                if side == 'BUY':
                    # For long positions, move stop up as price increases
                    new_stop = current_price * (1 - self.config.TRAILING_STOP_PCT)
                    if new_stop > trade['stop_loss']:
                        # Update the stop loss order
                        trade['stop_loss'] = new_stop
                        # In real implementation, you would cancel and replace the stop order
                else:
                    # For short positions, move stop down as price decreases
                    new_stop = current_price * (1 + self.config.TRAILING_STOP_PCT)
                    if new_stop < trade['stop_loss']:
                        # Update the stop loss order
                        trade['stop_loss'] = new_stop
                        # In real implementation, you would cancel and replace the stop order
                        
            except Exception as e:
                self.logger.error(f"Error adjusting stops for trade {trade_id}: {e}")
    
    def get_current_price(self, symbol):
        """Get current market price for a symbol"""
        # In real implementation, get the actual price from exchange
        return 50000  # Placeholder value
