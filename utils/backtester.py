"""
BACKTESTER - Simplified Working Version
"""

import pandas as pd
import numpy as np
from datetime import timedelta

class Backtester:
    def __init__(self, cot_data=None, price_data=None):
        self.cot_data = cot_data.copy() if cot_data is not None else None
        self.price_data = price_data.copy() if price_data is not None else None
    
    def align_cot_with_prices(self):
        """Align COT dates with price data"""
        if self.price_data is None or self.cot_data is None:
            return None
        
        cot_df = self.cot_data.copy()
        price_df = self.price_data.copy()
        
        # Ensure datetime
        cot_df['cot_date'] = pd.to_datetime(cot_df['cot_date'])
        price_df['date'] = pd.to_datetime(price_df['date'])
        
        # Sort
        cot_df = cot_df.sort_values('cot_date')
        price_df = price_df.sort_values('date')
        
        aligned_data = []
        
        for i in range(len(cot_df) - 1):
            cot_date = cot_df.iloc[i]['cot_date']
            cot_net = cot_df.iloc[i]['commercial_net']
            
            # Find entry price
            entry_mask = price_df['date'] > cot_date
            if not entry_mask.any():
                continue
                
            entry_row = price_df[entry_mask].iloc[0]
            entry_date = entry_row['date']
            entry_price = entry_row['price']
            
            # Find exit price (1 week later)
            exit_date_target = cot_date + timedelta(days=7)
            exit_mask = price_df['date'] >= exit_date_target
            
            if not exit_mask.any():
                continue
                
            exit_row = price_df[exit_mask].iloc[0]
            exit_date = exit_row['date']
            exit_price = exit_row['price']
            
            # Calculate returns
            price_change = exit_price - entry_price
            pips = price_change * 1000  # USD/ZAR: 1 pip = 0.001
            pct_return = (exit_price - entry_price) / entry_price * 100
            
            aligned_data.append({
                'cot_date': cot_date,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'commercial_net': cot_net,
                'pips': pips,
                'pct_return': pct_return
            })
        
        if not aligned_data:
            return None
        
        return pd.DataFrame(aligned_data)
    
    def backtest_threshold(self, threshold=-50000, capital=10000):
        """Backtest with threshold"""
        aligned_df = self.align_cot_with_prices()
        
        if aligned_df is None or len(aligned_df) == 0:
            return None
        
        # Create signals
        aligned_df['signal'] = (aligned_df['commercial_net'] < threshold).astype(int)
        
        # Filter trades
        trades_df = aligned_df[aligned_df['signal'] == 1].copy()
        
        if len(trades_df) == 0:
            return None
        
        # Apply costs
        spread_pips = 3
        trades_df['net_pips'] = trades_df['pips'] - spread_pips
        
        # Calculate profits
        trades_df['trade_profit'] = trades_df['net_pips'] * 10  # $10 per pip per lot
        trades_df['cumulative_profit'] = trades_df['trade_profit'].cumsum()
        trades_df['equity'] = capital + trades_df['cumulative_profit']
        trades_df['win'] = trades_df['net_pips'] > 0
        
        return trades_df
    
    def get_strategy_stats(self, threshold=-50000):
        """Get performance stats"""
        trades_df = self.backtest_threshold(threshold)
        
        if trades_df is None or len(trades_df) == 0:
            return None
        
        pips = trades_df['net_pips']
        profits = trades_df['trade_profit']
        
        # Drawdown
        equity = trades_df['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Calculate stats
        stats = {
            'total_trades': len(trades_df),
            'winning_trades': len(pips[pips > 0]),
            'losing_trades': len(pips[pips < 0]),
            'win_rate': round((pips > 0).mean() * 100, 1),
            'avg_win_pips': round(pips[pips > 0].mean(), 1) if len(pips[pips > 0]) > 0 else 0,
            'avg_loss_pips': round(abs(pips[pips < 0].mean()), 1) if len(pips[pips < 0]) > 0 else 0,
            'total_pips': round(pips.sum(), 1),
            'total_profit': round(profits.sum(), 0),
            'max_win_pips': round(pips.max(), 1),
            'max_loss_pips': round(pips.min(), 1),
            'profit_factor': round(abs(pips[pips > 0].sum() / pips[pips < 0].sum()), 2) if pips[pips < 0].sum() != 0 else 0,
            'max_drawdown_pct': round(max_drawdown, 2),
            'avg_return_pct': round(trades_df['pct_return'].mean(), 3),
            'final_equity': round(equity.iloc[-1], 2),
            'roi_pct': round(((equity.iloc[-1] - 10000) / 10000 * 100), 1)
        }
        
        # Simple Sharpe ratio
        returns = trades_df['pct_return'] / 100
        if len(returns) > 1 and returns.std() > 0:
            stats['sharpe_ratio'] = round((returns.mean() / returns.std()) * np.sqrt(52), 2)
        else:
            stats['sharpe_ratio'] = 0
        
        return stats
