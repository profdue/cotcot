class TradeCalculator:
    def __init__(self, account_balance=150, risk_percent=0.5):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
    
    def calculate_limit_order(self, direction, support, resistance):
        """Calculate limit order parameters"""
        if direction.upper() == "BUY":
            return {
                'order_type': 'BUY LIMIT',
                'entry': round(support + 0.0010, 4),  # Just above support
                'stop_loss': round(support - 0.0020, 4),  # 20 pips below
                'take_profit': round(support + 0.0050, 4),  # 50 pips above (2.5:1)
                'risk_pips': 30,
                'reward_pips': 50
            }
        elif direction.upper() == "SELL":
            return {
                'order_type': 'SELL LIMIT',
                'entry': round(resistance - 0.0010, 4),  # Just below resistance
                'stop_loss': round(resistance + 0.0020, 4),  # 20 pips above
                'take_profit': round(resistance - 0.0050, 4),  # 50 pips below (2.5:1)
                'risk_pips': 30,
                'reward_pips': 50
            }
        else:
            return None
    
    def get_risk_details(self, order_params):
        """Get risk management details"""
        if not order_params:
            return {}
        
        risk_amount = self.account_balance * (self.risk_percent / 100)
        
        return {
            'position_size': 0.01,  # Fixed for $150 accounts
            'risk_amount': round(risk_amount, 2),
            'risk_percent': self.risk_percent,
            'account_balance': self.account_balance
        }
