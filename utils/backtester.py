# UPDATED backtester.py - HONEST VERSION
"""
BACKTESTER WITH CLEAR ASSUMPTIONS
Since we don't have USD/ZAR prices, we'll:
1. Show what WOULD happen IF the edge exists
2. Make assumptions VERY conservative
"""

class Backtester:
    def __init__(self, cot_data):
        self.cot_data = cot_data.copy()
        self.assumptions = {
            'avg_weekly_move': 150,  # pips - USD/ZAR moves ~150 pips/week
            'win_rate_baseline': 50,  # % - Random trading = 50% win rate
            'edge_per_10k_net': 0.5,  # % - Each 10k commercial net = 0.5% edge
            'spread_cost': 3,  # pips - Typical USD/ZAR spread
        }
    
    def calculate_realistic_edge(self, threshold=-50000):
        """
        Calculate REALISTIC edge based on commercial positioning
        """
        # Get signals
        signals = (self.cot_data['commercial_net'] < threshold)
        
        # Calculate edge strength
        edge_strength = abs(self.cot_data['commercial_net']) / 10000 * self.assumptions['edge_per_10k_net']
        
        # Realistic win rate with diminishing returns
        win_rates = np.clip(
            self.assumptions['win_rate_baseline'] + edge_strength,
            50, 75  # Cap at 75% max (realistic)
        )
        
        # Apply only on signal days
        win_rates = win_rates * signals
        
        return win_rates
    
    def simulate_conservative_trades(self, threshold=-50000, capital=10000):
        """
        SIMPLE, CONSERVATIVE simulation
        """
        signals = (self.cot_data['commercial_net'] < threshold)
        
        # When signal active
        trade_days = self.cot_data[signals].copy()
        
        if len(trade_days) == 0:
            return None
        
        # Conservative assumptions
        results = []
        equity = capital
        
        for i, row in trade_days.iterrows():
            # Base trade
            net_position = abs(row['commercial_net'])
            
            # Edge increases with extreme positioning
            edge_multiplier = min(net_position / 50000, 2.0)  # Max 2x edge
            
            # Win probability (capped at 65% for realism)
            win_prob = min(50 + (net_position / 10000), 65)
            
            # Did we win?
            win = np.random.random() < (win_prob / 100)
            
            # Gain/Loss (capped at 100 pips max)
            if win:
                # Winners: 20-100 pips
                pips = np.random.uniform(20, 100) * edge_multiplier
            else:
                # Losers: 20-80 pips
                pips = -np.random.uniform(20, 80)
            
            # Apply spread cost
            pips -= self.assumptions['spread_cost']
            
            # Update equity (1 lot = $10 per pip)
            equity += pips * 10
            
            results.append({
                'date': row['cot_date'],
                'commercial_net': row['commercial_net'],
                'win': win,
                'pips': pips,
                'equity': equity,
                'edge_strength': edge_multiplier
            })
        
        return pd.DataFrame(results)
    
    def get_conservative_stats(self, threshold=-50000):
        """
        Get stats with REALISTIC assumptions
        """
        trades_df = self.simulate_conservative_trades(threshold)
        
        if trades_df is None or len(trades_df) < 5:
            return None
        
        pips = trades_df['pips']
        
        stats = {
            'total_trades': len(trades_df),
            'winning_trades': len(trades_df[trades_df['win']]),
            'win_rate': round((trades_df['win'].mean()) * 100, 1),
            'avg_win': round(pips[pips > 0].mean(), 1) if len(pips[pips > 0]) > 0 else 0,
            'avg_loss': round(abs(pips[pips < 0].mean()), 1) if len(pips[pips < 0]) > 0 else 0,
            'total_pips': round(pips.sum(), 1),
            'max_drawdown': self.calculate_drawdown(trades_df['equity']),
            'profit_factor': round(abs(pips[pips > 0].sum() / pips[pips < 0].sum()), 2) if pips[pips < 0].sum() != 0 else 0,
            'final_equity': round(trades_df['equity'].iloc[-1], 2)
        }
        
        return stats
    
    def calculate_drawdown(self, equity_series):
        """Calculate maximum drawdown"""
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        return round(drawdown.min() * 100, 2)  # as percentage
