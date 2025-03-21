#!/usr/bin/env python3
"""
Data Processor - Handles market data processing and indicators
"""
import pandas as pd
import numpy as np
import ta
import logging

class DataProcessor:
    """
    Processes market data and calculates indicators
    """
    
    def __init__(self, connection, config):
        self.connection = connection
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache for data
        self.data_cache = {}
        self.last_update = {}
    
    def get_latest_data(self, symbol=None, timeframe=None, limit=500):
        """Get latest market data and calculate indicators"""
        if symbol is None:
            symbol = self.config.SYMBOL
            
        if timeframe is None:
            timeframe = self.config.DEFAULT_TIMEFRAME
        
        # Check if we need to update the data
        current_time = pd.Timestamp.now()
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key in self.last_update:
            # Calculate seconds since last update
            seconds_since_update = (current_time - self.last_update[cache_key]).total_seconds()
            
            # Only update if enough time has passed (based on timeframe)
            if seconds_since_update < self.config.TIMEFRAMES[timeframe] / 2:
                return self.data_cache[cache_key]
        
        # Update data
        try:
            # Get candlestick data
            klines = self.connection.get_klines(symbol, timeframe, limit)
            
            # Convert to DataFrame
            df = self._klines_to_dataframe(klines)
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Update cache
            self.data_cache[cache_key] = df
            self.last_update[cache_key] = current_time
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}", exc_info=True)
            
            # Return cached data if available, otherwise empty DataFrame
            if cache_key in self.data_cache:
                return self.data_cache[cache_key]
            else:
                return pd.DataFrame()
    
    def _klines_to_dataframe(self, klines):
        """Convert Binance klines data to pandas DataFrame"""
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convert types
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Set index
        df.set_index('open_time', inplace=True)
        
        return df
    
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        # Make sure we have data
        if df.empty:
            return df
            
        # Moving Averages
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['sma_200'] = ta.trend.sma_indicator(df['close'], window=200)
        df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd_line'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_middle'] = bollinger.bollinger_mavg()
        df['bb_lower'] = bollinger.bollinger_lband()
        
        # Volume indicators
        df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
        
        # Calculate VWAP
        df = self.calculate_vwap(df)
        
        # Calculate pivot points
        df = self.calculate_pivot_points(df)
        
        return df
    
    def calculate_vwap(self, df):
        """Calculate VWAP (Volume Weighted Average Price)"""
        # Reset index to use open_time as a column
        df_copy = df.reset_index()
        
        # Make sure we start with the day's first candle 
        # This is a simplification - real implementation would use actual day boundaries
        # Extract the date from open_time
        df_copy['date'] = df_copy['open_time'].dt.date
        
        # Group by date and calculate VWAP
        df_copy['vwap'] = 0.0
        
        # Loop through each day
        for date, group in df_copy.groupby('date'):
            # Calculate cumulative values for the day
            group = group.copy()
            group['cum_vol'] = group['volume'].cumsum()
            group['cum_vol_price'] = (group['volume'] * (group['high'] + group['low'] + group['close']) / 3).cumsum()
            
            # Calculate VWAP
            group['vwap'] = group['cum_vol_price'] / group['cum_vol']
            
            # Update the main DataFrame
            df_copy.loc[group.index, 'vwap'] = group['vwap']
        
        # Restore the index
        df_copy.set_index('open_time', inplace=True)
        
        # Keep only the original columns plus VWAP
        df_copy = df_copy[df.columns.tolist() + ['vwap']]
        
        return df_copy
    
    def calculate_pivot_points(self, df):
        """Calculate pivot points"""
        # This is a simplified implementation - real pivot points should use properly defined period boundaries
        
        # Create a copy to avoid modifying the original dataframe
        df_copy = df.copy()
        
        # Define the lookback period for pivot calculation
        lookback = self.config.PIVOT_POINT.get('lookback_period', 1)
        
        # Calculate traditional pivot points
        df_copy['pivot'] = (df_copy['high'].shift(lookback) + df_copy['low'].shift(lookback) + df_copy['close'].shift(lookback)) / 3
        df_copy['r1'] = 2 * df_copy['pivot'] - df_copy['low'].shift(lookback)
        df_copy['s1'] = 2 * df_copy['pivot'] - df_copy['high'].shift(lookback)
        df_copy['r2'] = df_copy['pivot'] + (df_copy['high'].shift(lookback) - df_copy['low'].shift(lookback))
        df_copy['s2'] = df_copy['pivot'] - (df_copy['high'].shift(lookback) - df_copy['low'].shift(lookback))
        df_copy['r3'] = df_copy['high'].shift(lookback) + 2 * (df_copy['pivot'] - df_copy['low'].shift(lookback))
        df_copy['s3'] = df_copy['low'].shift(lookback) - 2 * (df_copy['high'].shift(lookback) - df_copy['pivot'])
        
        return df_copy
    
    def detect_gaps(self, df):
        """Detect price gaps between candles"""
        # Calculate gaps
        df['gap_up'] = df['open'] > df['close'].shift(1) * 1.005  # 0.5% gap up
        df['gap_down'] = df['open'] < df['close'].shift(1) * 0.995  # 0.5% gap down
        df['gap_size'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1) * 100
        
        return df
