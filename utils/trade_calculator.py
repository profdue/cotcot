class TradeCalculator:
    def __init__(self, account_balance=150, risk_percent=0.5):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.risk_amount = account_balance * (risk_percent / 100)
        
    def calculate_position_size(self, entry_price, stop_loss, direction="BUY"):
        """
        Calculate position size based on risk
        For USD/ZAR: 1 pip = 0.0001
        For 0.01 lots: 1 pip = $0.01 (approximately)
        """
        if direction == "BUY":
            risk_pips = (entry_price - stop_loss) * 10000
        else:  # SELL
            risk_pips = (stop_loss - entry_price) * 10000
        
        risk_pips = abs(risk_pips)
        
        if risk_pips == 0:
            return {"error": "Stop loss too close to entry"}
        
        # Simplified: For USD/ZAR, 0.01 lots = ~$0.01 per pip
        # More accurate calculation would need pip value formula
        pip_value = 0.01  # For 0.01 lots on USD/ZAR
        
        position_size = self.risk_amount / (risk_pips * pip_value)
        
        # Cap at 0.01 lots for small accounts
        position_size = min(position_size, 0.01)
        
        return {
            'risk_pips': int(risk_pips),
            'position_size': round(position_size, 4),
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
        
        return {
            'take_profit': round(take_profit, 4),
            'risk_pips': int(abs(risk_pips)),
            'reward_pips': int(abs(risk_pips) * risk_reward),
            'risk_reward_ratio': risk_reward
        }
    
    def generate_trade_plan(self, cot_signal, entry_price, recent_high, recent_low):
        """
        Generate complete trade plan based on COT signal
        """
        # Determine direction from COT signal
        if "BULLISH USD/ZAR" in cot_signal.get('usdzar_bias', ''):
            direction = "BUY"
            entry_zone = recent_low + 0.0010  # Just above support
            stop_loss = recent_low - 0.0020
        elif "BEARISH USD/ZAR" in cot_signal.get('usdzar_bias', ''):
            direction = "SELL"
            entry_zone = recent_high - 0.0010  # Just below resistance
            stop_loss = recent_high + 0.0020
        else:
            return {"error": "No clear signal from COT data"}
        
        # Calculate position size
        position_info = self.calculate_position_size(entry_zone, stop_loss, direction)
        
        # Calculate take profit
        tp_info = self.calculate_take_profit(entry_zone, stop_loss, direction)
        
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
            'cot_signal': cot_signal['usdzar_bias'],
            'signal_strength': cot_signal['signal_strength']
        }
