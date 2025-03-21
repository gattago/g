#!/usr/bin/env python3
"""
Ichimoku Kinko Hyo Strategy Implementation
"""
import numpy as np
import pandas as pd
from strategies.base_strategy import BaseStrategy

class IchimokuStrategy(BaseStrategy):
    """
    Ichimoku Kinko Hyo Strategy
    Uses cloud, conversion line, base line, and lagging span for trend identification
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "ichimoku"
        self.tenkan_period = config.ICHIMOKU['tenkan_period']
        self.kijun_period = config.ICHIMOKU['kijun_period'] 
        self.senkou_span_b_period = config.ICHIMOKU['senkou_span_b_period']
        self.displacement = config.ICHIMOKU['displacement']
    
    def calculate_ichimoku(self, df):
        """Calculate Ichimoku components"""
        # Tenkan-sen (Conversion Line): (highest high + lowest low) / 2 for the past n periods
        high_tenkan = df['high'].rolling(window=self.tenkan_period).max()
        low_tenkan = df['low'].rolling(window=self.tenkan_period).min()
        df['tenkan_sen'] = (high_tenkan + low_tenkan) / 2
        
        # Kijun-sen (Base Line): (highest high + lowest low) / 2 for the past n*3 periods
        high_kijun = df['high'].rolling(window=self.kijun_period).max()
        low_kijun = df['low'].rolling(window=self.kijun_period).min()
        df['kijun_sen'] = (high_kijun + low_kijun) / 2
        
        # Senkou Span A (Leading Span A): (Conversion Line + Base Line) / 2 (projected n periods forward)
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(self.displacement)
        
        # Senkou Span B (Leading Span B): (highest high + lowest low) / 2 for past n*6 periods (projected n periods forward)
        high_senkou = df['high'].rolling(window=self.senkou_span_b_period).max()
        low_senkou = df['low'].rolling(window=self.senkou_span_b_period).min()
        df['senkou_span_b'] = ((high_senkou + low_senkou) / 2).shift(self.displacement)
        
        # Chikou Span (Lagging Span): Current closing price projected n periods backward
        df['chikou_span'] = df['close'].shift(-self.displacement)
        
        return df
    
    def generate_signals(self, data):
        """Generate trading signals based on Ichimoku strategy"""
        df = data.copy()
        
        # Calculate Ichimoku components
        df = self.calculate_ichimoku(df)
        
        # Prepare signals array
        signals = []
        
        # Check for enough data to generate valid signals
        if len(df) < self.senkou_span_b_period + self.displacement:
            self.logger.warning(f"Not enough data for Ichimoku strategy: need {self.senkou_span_b_period + self.displacement} candles")
            return signals
        
        # Calculate signal
        current_price = df['close'].iloc[-1]
        tenkan = df['tenkan_sen'].iloc[-1]
        kijun = df['kijun_sen'].iloc[-1]
        span_a = df['senkou_span_a'].iloc[-1]
        span_b = df['senkou_span_b'].iloc[-1]
        chikou = df['chikou_span'].iloc[-self.displacement-1] if len(df) > self.displacement+1 else None
        
        # Get previous values for trend confirmation
        prev_tenkan = df['tenkan_sen'].iloc[-2]
        prev_kijun = df['kijun_sen'].iloc[-2]
        
        # Define cloud
        cloud_top = max(span_a, span_b)
        cloud_bottom = min(span_a, span_b)
        bullish_cloud = span_a > span_b
        
        # BUY Signal Conditions
        buy_signal = False
        sell_signal = False
        
        # Traditional TK Cross (Tenkan crosses above Kijun)
        tk_cross_bullish = tenkan > kijun and prev_tenkan <= prev_kijun
        
        # Price above the cloud
        price_above_cloud = current_price > cloud_top
        
        # Chikou Span above price from n periods ago
        chikou_bullish = chikou is not None and chikou > df['close'].iloc[-2*self.displacement-1] if len(df) > 2*self.displacement+1 else False
        
        # Full bullish condition
        buy_signal = tk_cross_bullish and price_above_cloud and bullish_cloud and chikou_bullish
        
        # SELL Signal Conditions (opposite of buy)
        tk_cross_bearish = tenkan < kijun and prev_tenkan >= prev_kijun
        price_below_cloud = current_price < cloud_bottom
        chikou_bearish = chikou is not None and chikou < df['close'].iloc[-2*self.displacement-1] if len(df) > 2*self.displacement+1 else False
        
        sell_signal = tk_cross_bearish and price_below_cloud and not bullish_cloud and chikou_bearish
        
        # Generate signals
        if buy_signal:
            signals.append({
                'strategy': self.name,
                'symbol': self.config.SYMBOL,
                'side': 'BUY',
                'price': current_price,
                'quantity': self.calculate_position_size(current_price, 'BUY'),
                'stop_loss': kijun * 0.99,  # Stop loss just below Kijun-sen
                'take_profit': current_price + (current_price - kijun) * 2,  # 1:2 risk-reward
                'timestamp': pd.Timestamp.now()
            })
            
        if sell_signal:
            signals.append({
                'strategy': self.name,
                'symbol': self.config.SYMBOL,
                'side': 'SELL',
                'price': current_price,
                'quantity': self.calculate_position_size(current_price, 'SELL'),
                'stop_loss': kijun * 1.01,  # Stop loss just above Kijun-sen
                'take_profit': current_price - (kijun - current_price) * 2,  # 1:2 risk-reward
                'timestamp': pd.Timestamp.now()
            })
            
        return signals
    
    def calculate_position_size(self, price, side):
        """Calculate position size based on risk parameters"""
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
        # In a real implementation, this would get the actual balance
        # Here we return a placeholder value
        return 10000  # Placeholder - should be replaced with actual balance retrieval
