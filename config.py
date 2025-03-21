#!/usr/bin/env python3
"""
Configuration settings for the Binance Testnet Trading Bot
"""

class Config:
    def __init__(self, config_file=None):
        # API Configuration (replace with your testnet keys)
        self.API_KEY = "your_testnet_api_key_here"
        self.API_SECRET = "your_testnet_api_secret_here"
        
        # Trading parameters
        self.SYMBOL = "BTCUSDT"  # Trading pair
        self.TIMEFRAMES = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400
        }
        self.DEFAULT_TIMEFRAME = "5m"
        self.LOOP_INTERVAL = 60  # Seconds between each trading check
        
        # Risk Management
        self.MAX_POSITION_SIZE = 0.01  # Maximum position size in BTC
        self.RISK_PER_TRADE = 0.01     # 1% of account per trade
        self.MAX_OPEN_TRADES = 3       # Maximum number of concurrent open trades
        self.USE_STOP_LOSS = True
        self.STOP_LOSS_PCT = 0.02      # 2% stop loss
        self.TAKE_PROFIT_PCT = 0.04    # 4% take profit
        self.USE_TRAILING_STOP = True
        self.TRAILING_STOP_PCT = 0.01  # 1% trailing stop
        
        # Strategy Parameters
        self.ENABLED_STRATEGIES = [
            "ichimoku", "pivot_point", "vwap", "gap", "pullback", 
            "range", "reversal", "breakout", "momentum", "scalping"
        ]
        
        # Ichimoku Settings
        self.ICHIMOKU = {
            "tenkan_period": 9,
            "kijun_period": 26,
            "senkou_span_b_period": 52,
            "displacement": 26
        }
        
        # Pivot Point Settings
        self.PIVOT_POINT = {
            "method": "traditional",  # traditional, fibonacci, camarilla, woodie
            "lookback_period": 1
        }
        
        # VWAP Settings
        self.VWAP = {
            "period": "1d",  # Calculate VWAP over this period
            "std_dev_multiplier": 2.0  # Standard deviation bands multiplier
        }
        
        # Gap Trading Settings
        self.GAP = {
            "min_gap_percent": 0.5,  # Minimum gap size to consider (%)
            "max_gap_percent": 5.0   # Maximum gap size to consider (%)
        }
        
        # Pullback Settings
        self.PULLBACK = {
            "trend_period": 50,      # Period to determine overall trend
            "pullback_threshold": 0.3 # Pullback strength threshold (0-1)
        }
        
        # News Trading Settings
        self.NEWS = {
            "api_key": "your_news_api_key",
            "sources": ["cryptopanic", "twitter"],
            "sentiment_threshold": 0.6  # Minimum sentiment score to trigger trade
        }
        
        # Range Trading Settings
        self.RANGE = {
            "lookback_period": 20,  # Candles to look back for range
            "range_deviation": 0.05  # 5% deviation to confirm range
        }
        
        # Reversal Settings
        self.REVERSAL = {
            "overbought_threshold": 70,  # RSI overbought
            "oversold_threshold": 30,    # RSI oversold
            "confirmation_candles": 2    # Number of candles for confirmation
        }
        
        # Breakout Settings
        self.BREAKOUT = {
            "lookback_period": 20,    # Period for support/resistance calculation
            "volume_multiplier": 1.5,  # Required volume increase for valid breakout
            "fake_breakout_filter": True
        }
        
        # Momentum Settings
        self.MOMENTUM = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30
        }
        
        # Scalping Settings
        self.SCALPING = {
            "profit_pips": 10,         # Target profit in pips
            "max_spread": 3,           # Maximum allowed spread
            "max_trade_duration": 300  # Maximum trade duration in seconds
        }
        
        # Override with config file if specified
        if config_file:
            self._load_from_file(config_file)
    
    def _load_from_file(self, config_file):
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                config_data = eval(f.read())
            for key, value in config_data.items():
                setattr(self, key, value)
        except Exception as e:
            print(f"Error loading config file: {e}")
