#!/usr/bin/env python3
"""
Binance Testnet Trading Bot - Main Entry Point
"""
import time
import logging
from datetime import datetime
import argparse

from config import Config
from binance_connection import BinanceConnection
from strategy_manager import StrategyManager
from risk_manager import RiskManager
from data_processor import DataProcessor
from utils import setup_logger

def parse_arguments():
    parser = argparse.ArgumentParser(description='Binance Testnet Trading Bot')
    parser.add_argument('--config', type=str, default='config.py',
                        help='Path to configuration file')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--strategies', type=str, 
                        help='Comma-separated list of strategies to use')
    parser.add_argument('--symbol', type=str,
                        help='Trading symbol (e.g. BTCUSDT)')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_level)
    logger.info("Starting Binance Testnet Trading Bot")
    
    # Load configuration
    config = Config(args.config)
    if args.symbol:
        config.SYMBOL = args.symbol
    
    # Connect to Binance Testnet
    connection = BinanceConnection(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        testnet=True
    )
    
    # Initialize components
    data_processor = DataProcessor(connection, config)
    risk_manager = RiskManager(connection, config)
    
    # Initialize strategy manager
    strategy_manager = StrategyManager(
        connection=connection,
        data_processor=data_processor,
        risk_manager=risk_manager,
        config=config
    )
    
    # Override strategies if specified in args
    if args.strategies:
        enabled_strategies = [s.strip() for s in args.strategies.split(',')]
        strategy_manager.set_enabled_strategies(enabled_strategies)
    
    logger.info(f"Trading {config.SYMBOL} with strategies: {strategy_manager.get_enabled_strategies()}")
    logger.info(f"Initial account balance: {connection.get_account_balance()}")
    
    # Main trading loop
    try:
        while True:
            # Process market data
            data = data_processor.get_latest_data()
            
            # Execute trading strategies
            signals = strategy_manager.generate_signals(data)
            
            # Execute trades based on signals
            for signal in signals:
                if risk_manager.validate_trade(signal):
                    connection.execute_trade(signal)
                    logger.info(f"Executed trade: {signal}")
                else:
                    logger.info(f"Trade rejected by risk manager: {signal}")
            
            # Wait for next iteration
            time.sleep(config.LOOP_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Shutting down bot...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    finally:
        # Print final account state
        balance = connection.get_account_balance()
        logger.info(f"Final account balance: {balance}")

if __name__ == "__main__":
    main()
