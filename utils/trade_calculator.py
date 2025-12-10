class TradeCalculator:
    def __init__(self, account_balance=150, risk_percent=0.5):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
    
    def generate_simple_plan(self, cot_signal, today_low, today_high):
        """Generate super simple trade plan"""
        if not cot_signal or 'error' in cot_signal:
            return {'error': 'No COT signal'}
        
        bias = cot_signal.get('usdzar_bias', '').upper()
        
        if "BULLISH" in bias:
            return {
                'direction': 'BUY',
                'entry': round(today_low + 0.0010, 4),
                'stop_loss': round(today_low - 0.0020, 4),
                'take_profit': round(today_low + 0.0050, 4),
                'risk_amount': round(self.account_balance * (self.risk_percent / 100), 2),
                'position_size': 0.01
            }
        elif "BEARISH" in bias:
            return {
                'direction': 'SELL',
                'entry': round(today_high - 0.0010, 4),
                'stop_loss': round(today_high + 0.0020, 4),
                'take_profit': round(today_high - 0.0050, 4),
                'risk_amount': round(self.account_balance * (self.risk_percent / 100), 2),
                'position_size': 0.01
            }
        else:
            return {'error': 'No clear direction'}
