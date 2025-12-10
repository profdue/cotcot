class TradeCalculator:
    def __init__(self, account_balance=150, risk_percent=0.5):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.risk_amount = account_balance * (risk_percent / 100)
        
    def calculate_position_size(self, entry_price, stop_loss, direction="BUY"):
        """
        Calculate position size based on risk
        For USD/ZAR: 1 pip = 0.0001
        For 0.01 lots: 1 pip = ~$0.01
        """
        if direction == "BUY":
            risk_pips = (entry_price - stop_loss) * 10000
        else:  # SELL
            risk_pips = (stop_loss - entry_price) * 10000
        
        risk_pips = abs(risk_pips)
        
        if risk_pips <= 0:
            return {
                'error': 'Stop loss too close to entry or invalid',
                'risk_pips': 0,
                'position_size': 0,
                'risk_amount': self.risk_amount
            }
        
        # Simplified: For USD/ZAR, 0.01 lots = ~$0.01 per pip
        pip_value = 0.01  # For 0.01 lots on USD/ZAR
        
        position_size = self.risk_amount / (risk_pips * pip_value)
        
        # Cap at 0.01 lots for small accounts (safety)
        if self.account_balance < 300:
            position_size = min(position_size, 0.01)
        
        # Round to nearest 0.0001 for lot size
        position_size = round(position_size, 4)
        
        return {
            'risk_pips': int(risk_pips),
            'position_size': position_size,
            'risk_amount': round(self.risk_amount, 2),
            'pip_value': pip_value
        }
    
    def calculate_take_profit(self, entry_price, stop_loss, direction="BUY", risk_reward=2.0):
        """Calculate take profit based on risk:reward ratio"""
        if direction == "BUY":
            risk_pips = (entry_price - stop_loss) * 10000
            take_profit = entry_price + (risk_pips * risk_reward / 10000)
        else:  # SELL
            risk_pips = (stop_loss - entry_price) * 10000
            take_profit = entry_price - (risk_pips * risk_reward / 10000)
        
        risk_pips = abs(risk_pips)
        
        return {
            'take_profit': round(take_profit, 4),
            'risk_pips': int(risk_pips),
            'reward_pips': int(risk_pips * risk_reward),
            'risk_reward_ratio': risk_reward
        }
    
    def generate_trade_plan(self, cot_signal, current_price, recent_high, recent_low):
        """
        Generate complete trade plan based on COT signal
        
        Returns:
        {
            'direction': 'BUY'/'SELL',
            'entry_zone': float,
            'stop_loss': float,
            'take_profit': float,
            'risk_pips': int,
            'reward_pips': int,
            'risk_reward_ratio': float,
            'position_size': float,
            'risk_amount': float,
            'cot_signal': str,
            'signal_strength': str
        }
        """
        # Check if we have valid COT signal
        if not cot_signal or 'error' in cot_signal:
            return {'error': 'Invalid COT signal'}
        
        # Determine direction from COT signal
        usdzar_bias = cot_signal.get('usdzar_bias', '').upper()
        
        if "BULLISH" in usdzar_bias:
            direction = "BUY"
            # Entry just above support (recent low)
            entry_zone = recent_low + 0.0010
            stop_loss = recent_low - 0.0020
        elif "BEARISH" in usdzar_bias:
            direction = "SELL"
            # Entry just below resistance (recent high)
            entry_zone = recent_high - 0.0010
            stop_loss = recent_high + 0.0020
        else:
            return {'error': 'No clear signal from COT data'}
        
        # Validate levels
        if direction == "BUY" and entry_zone >= current_price:
            return {'error': f'Entry ({entry_zone:.4f}) is above current price ({current_price:.4f}) - wait for pullback'}
        elif direction == "SELL" and entry_zone <= current_price:
            return {'error': f'Entry ({entry_zone:.4f}) is below current price ({current_price:.4f}) - wait for rally'}
        
        # Calculate position size
        position_info = self.calculate_position_size(entry_zone, stop_loss, direction)
        
        if 'error' in position_info:
            return position_info
        
        # Calculate take profit (2:1 risk:reward)
        tp_info = self.calculate_take_profit(entry_zone, stop_loss, direction, risk_reward=2.0)
        
        return {
            'direction': direction,
            'entry_zone': round(entry_zone, 4),
            'stop_loss': round(stop_loss, 4),
            'take_profit': tp_info['take_profit'],
            'risk_pips': position_info['risk_pips'],
            'reward_pips': tp_info['reward_pips'],
            'risk_reward_ratio': tp_info['risk_reward_ratio'],
            'position_size': position_info['position_size'],
            'risk_amount': position_info['risk_amount'],
            'cot_signal': cot_signal.get('usdzar_bias', 'UNKNOWN'),
            'signal_strength': cot_signal.get('signal_strength', 'UNKNOWN')
        }
    
    def get_price_action_instructions(self, direction, entry_zone):
        """Get price action instructions for the trade"""
        if direction == "BUY":
            return {
                'wait_for': f"Price to reach {entry_zone:.4f}",
                'candle1': 'RED candle forming at support',
                'candle2': 'GREEN candle closing above red high',
                'action': 'Enter AFTER green candle closes',
                'warning': 'DO NOT enter during red candle - wait for confirmation'
            }
        else:
            return {
                'wait_for': f"Price to reach {entry_zone:.4f}",
                'candle1': 'GREEN candle forming at resistance',
                'candle2': 'RED candle closing below green low',
                'action': 'Enter AFTER red candle closes',
                'warning': 'DO NOT enter during green candle - wait for confirmation'
            }
