#!/usr/bin/env python3
"""
Strategy Manager - Manages all trading strategies
"""
import importlib
import logging

class StrategyManager:
    """
    Strategy Manager - Loads, initializes, and runs trading strategies
    """
    
    def __init__(self, connection, data_processor, risk_manager, config):
        self.connection = connection
        self.data_processor = data_processor
        self.risk_manager = risk_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.strategies = {}
        self.enabled_strategies = config.ENABLED_STRATEGIES
        
        # Load strategies
        self._load_strategies()
    
    def _load_strategies(self):
        """Load all enabled strategies"""
        strategy_modules = {
            "ichimoku": "strategies.ichimoku",
            "pivot_point": "strategies.pivot_point",
            "vwap": "strategies.vwap",
            "gap": "strategies.gap",
            "pullback": "strategies.pullback",
            "news": "strategies.news",
            "range": "strategies.range",
            "reversal": "strategies.reversal",
            "breakout": "strategies.breakout",
            "momentum": "strategies.momentum",
            "scalping": "strategies.scalping"
        }
        
        for strategy_name in self.enabled_strategies:
            try:
                if strategy_name not in strategy_modules:
                    self.logger.error(f"Strategy {strategy_name} not found")
                    continue
                
                module_path = strategy_modules[strategy_name]
                module = importlib.import_module(module_path)
                
                # Get the class name (convert snake_case to CamelCase + "Strategy")
                class_name = ''.join(word.title() for word in strategy_name.split('_')) + 'Strategy'
                
                # Get the strategy class from the module
                strategy_class = getattr(module, class_name)
                
                # Initialize the strategy
                strategy = strategy_class(self.config)
                
                # Add references to other components
                strategy.connection = self.connection
                strategy.risk_manager = self.risk_manager
                
                # Add to strategies dictionary
                self.strategies[strategy_name] = strategy
                self.logger.info(f"Successfully loaded strategy: {strategy_name}")
                
            except Exception as e:
                self.logger.error(f"Error loading strategy {strategy_name}: {e}", exc_info=True)
    
    def set_enabled_strategies(self, strategy_list):
        """Enable or disable strategies"""
        self.enabled_strategies = strategy_list
        # Reload strategies with the new list
        self._load_strategies()
    
    def get_enabled_strategies(self):
        """Return list of enabled strategies"""
        return self.enabled_strategies
    
    def generate_signals(self, data):
        """Generate trading signals from all enabled strategies"""
        all_signals = []
        
        for strategy_name in self.enabled_strategies:
            if strategy_name not in self.strategies:
                self.logger.warning(f"Strategy {strategy_name} not initialized")
                continue
                
            strategy = self.strategies[strategy_name]
            try:
                signals = strategy.generate_signals(data)
                all_signals.extend(signals)
            except Exception as e:
                self.logger.error(f"Error generating signals for {strategy_name}: {e}", exc_info=True)
        
        # Sort signals by strength/confidence if they have that attribute
        if all_signals and 'confidence' in all_signals[0]:
            all_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return all_signals
    
    def combine_signals(self, signals):
        """
        Combine signals from different strategies
        This can be used to implement more sophisticated signal combining logic
        """
        # Simple implementation: count buy vs sell signals
        buy_signals = [s for s in signals if s['side'] == 'BUY']
        sell_signals = [s for s in signals if s['side'] == 'SELL']
        
        # If more than 60% of signals are in one direction, go with it
        total_signals = len(signals)
        if total_signals == 0:
            return []
            
        buy_percentage = len(buy_signals) / total_signals
        sell_percentage = len(sell_signals) / total_signals
        
        combined_signals = []
        
        if buy_percentage > 0.6:
            # Create a combined buy signal
            if buy_signals:
                # Use the signal with highest confidence or first one
                best_signal = max(buy_signals, key=lambda x: x.get('confidence', 0)) if 'confidence' in buy_signals[0] else buy_signals[0]
                combined_signals.append(best_signal)
        
        if sell_percentage > 0.6:
            # Create a combined sell signal
            if sell_signals:
                # Use the signal with highest confidence or first one
                best_signal = max(sell_signals, key=lambda x: x.get('confidence', 0)) if 'confidence' in sell_signals[0] else sell_signals[0]
                combined_signals.append(best_signal)
        
        return combined_signals
