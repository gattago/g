#!/usr/bin/env python3
"""
Utility functions for the trading bot
"""
import logging
import json
from datetime import datetime

def setup_logger(level=logging.INFO):
    """Setup and configure logger"""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    
    # Create file handler
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fh = logging.FileHandler(f"trading_bot_{timestamp}.log")
    fh.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger

def calculate_risk_reward_ratio(entry, stop_loss, take_profit, side):
    """
    Calculate risk-reward ratio
    
    Args:
        entry (float): Entry price
        stop_loss (float): Stop loss price
        take_profit (float): Take profit price
        side (str): 'BUY' or 'SELL'
        
    Returns:
        float: Risk-reward ratio
    """
    if side.upper() == 'BUY':
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
    else:
        risk = abs(stop_loss - entry)
        reward = abs(entry - take_profit)
        
    if risk == 0:
        return 0
        
    return reward / risk

def save_trade_history(trade, filename="trade_history.json"):
    """Save trade to trade history file"""
    try:
        # Read existing trades
        try:
            with open(filename, 'r') as f:
                trades = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            trades = []
        
        # Add new trade
        trade_record = {
            "symbol": trade.get("symbol"),
            "side": trade.get("side"),
            "entry_price": trade.get("price"),
            "quantity": trade.get("quantity"),
            "stop_loss": trade.get("stop_loss"),
            "take_profit": trade.get("take_profit"),
            "strategy": trade.get("strategy"),
            "timestamp": datetime.now().isoformat(),
            "risk_reward_ratio": calculate_risk_reward_ratio(
                trade.get("price", 0), 
                trade.get("stop_loss", 0), 
                trade.get("take_profit", 0), 
                trade.get("side", "BUY")
            )
        }
        
        trades.append(trade_record)
        
        # Write back to file
        with open(filename, 'w') as f:
            json.dump(trades, f, indent=2)
            
    except Exception as e:
        logging.error(f"Error saving trade history: {e}")

def load_trade_history(filename="trade_history.json"):
    """Load trade history"""
    try:
        with open(filename, 'r') as f:
            trades = json.load(f)
        return trades
    except (FileNotFoundError, json.JSONDecodeError):
        return []
