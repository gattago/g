# Binance Testnet Trading Bot

A comprehensive trading bot for Binance testnet that implements multiple trading strategies including Ichimoku Kinko Hyo, Pivot Point, VWAP, Gap Trading, Pullback, News, Range, Reversal, Breakout, Momentum Trading and Scalping.

## Features

- Connects to Binance Testnet API
- Implements 11 different trading strategies
- Strategy combination and selection framework
- Risk management system
- Real-time market data processing
- Customizable configuration
- Logging and performance tracking

## Installation

1. Clone this repository
2. Install required packages: `pip install -r requirements.txt`
3. Configure your API keys in `config.py`
4. Run the bot: `python main.py`

## Configuration

Edit `config.py` to set:
- API keys
- Trading pairs
- Risk parameters
- Strategy parameters
- Execution settings

## Strategies

1. **Ichimoku Kinko Hyo**: Uses cloud, conversion line, base line, and lagging span for trend identification
2. **Pivot Point**: Based on previous period's high, low, and close to identify support/resistance
3. **VWAP**: Volume Weighted Average Price for intraday trading
4. **Gap Trading**: Identifies and trades price gaps
5. **Pullback Trading**: Trades temporary price reversals within a larger trend
6. **News Trading**: Analyzes market sentiment from news data
7. **Range Trading**: Trades between support and resistance levels
8. **Reversal Trading**: Identifies trend reversals
9. **Breakout Trading**: Trades when price breaks through support/resistance
10. **Momentum Trading**: Trades based on strength of price movements
11. **Scalping**: Makes multiple small profits on short-term price changes

## Risk Management

The bot includes a comprehensive risk management system that:
- Controls position sizing
- Sets stop losses and take profit levels
- Implements trailing stops
- Manages overall exposure

## Disclaimer

This bot is for educational purposes only. Trading cryptocurrencies involves significant risk.
