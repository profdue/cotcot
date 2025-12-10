"""
CORRECTED BACKTESTER with Proper Logic
Signal: commercial_net < threshold means "when EXTREMELY short"
"""

import pandas as pd
import numpy as np
from datetime import timedelta

class Backtester:
    def __init__(self, cot_data=None, price_data=None):
        """
        Initialize with corrected understanding:
        threshold = EXTREME level (e.g., -60000 = extremely short)
        Signal triggers when commercial_net < threshold (more negative)
        """
        self.cot_data = cot_data.copy() if cot_data is not None else None
        self.price_data = price_data.copy() if price_data is not None else None
    
    def align_cot_with_prices(self):
        """Align COT dates with price data for weekly trades"""
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
            
            # Find entry price (next trading day)
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
                'pct_return': pct_return,
                'price_change': price_change,
                'holding_days': (exit_date - entry_date).days
            })
        
        if not aligned_data:
            return None
        
        return pd.DataFrame(aligned_data)
    
    def backtest_threshold(self, threshold=-60000, capital=10000, 
                          risk_per_trade=0.005, stop_loss_pips=100):
        """
        CORRECTED: Backtest when commercials are EXTREMELY short
        threshold = extreme level (e.g., -60000)
        Signal: commercial_net < threshold (more negative than threshold)
        """
        aligned_df = self.align_cot_with_prices()
        
        if aligned_df is None or len(aligned_df) == 0:
            return None
        
        # CORRECT SIGNAL LOGIC: When EXTREMELY short
        aligned_df['signal'] = (aligned_df['commercial_net'] < threshold).astype(int)
        
        # Filter trades
        trades_df = aligned_df[aligned_df['signal'] == 1].copy()
        
        if len(trades_df) == 0:
            return None
        
        # Apply trading costs
        spread_pips = 3  # USD/ZAR typical spread
        trades_df['gross_pips'] = trades_df['pips']
        trades_df['net_pips'] = trades_df['pips'] - spread_pips
        
        # Apply stop loss
        trades_df['stop_loss_hit'] = trades_df['net_pips'] < -stop_loss_pips
        trades_df['adjusted_pips'] = np.where(
            trades_df['stop_loss_hit'],
            -stop_loss_pips,
            trades_df['net_pips']
        )
        
        # Position sizing with stop loss
        risk_amount = capital * risk_per_trade
        pips_per_dollar = 10  # USD/ZAR: $10 per pip per standard lot
        position_size = risk_amount / (stop_loss_pips * pips_per_dollar)
        
        # Calculate profit/loss
        trades_df['trade_profit'] = trades_df['adjusted_pips'] * pips_per_dollar * position_size
        trades_df['cumulative_profit'] = trades_df['trade_profit'].cumsum()
        trades_df['equity'] = capital + trades_df['cumulative_profit']
        trades_df['win'] = trades_df['adjusted_pips'] > 0
        
        # Calculate drawdown
        trades_df['peak'] = trades_df['equity'].expanding().max()
        trades_df['drawdown'] = (trades_df['equity'] - trades_df['peak']) / trades_df['peak'] * 100
        
        return trades_df
    
    def get_strategy_stats(self, threshold=-60000, risk_per_trade=0.005, stop_loss_pips=100):
        """Get performance statistics with corrected logic"""
        trades_df = self.backtest_threshold(
            threshold=threshold,
            risk_per_trade=risk_per_trade,
            stop_loss_pips=stop_loss_pips
        )
        
        if trades_df is None or len(trades_df) == 0:
            return None
        
        pips = trades_df['adjusted_pips']
        profits = trades_df['trade_profit']
        
        # Calculate metrics
        stats = {
            'threshold': threshold,
            'total_trades': len(trades_df),
            'winning_trades': len(pips[pips > 0]),
            'losing_trades': len(pips[pips < 0]),
            'stop_loss_hits': trades_df['stop_loss_hit'].sum(),
            'win_rate': round((pips > 0).mean() * 100, 1),
            'avg_win_pips': round(pips[pips > 0].mean(), 1) if len(pips[pips > 0]) > 0 else 0,
            'avg_loss_pips': round(abs(pips[pips < 0].mean()), 1) if len(pips[pips < 0]) > 0 else 0,
            'total_pips': round(pips.sum(), 1),
            'total_profit': round(profits.sum(), 0),
            'profit_factor': round(abs(pips[pips > 0].sum() / pips[pips < 0].sum()), 2) if pips[pips < 0].sum() != 0 else 0,
            'max_drawdown_pct': round(trades_df['drawdown'].min(), 2),
            'avg_return_pct': round(trades_df['pct_return'].mean(), 3),
            'final_equity': round(trades_df['equity'].iloc[-1], 2),
            'roi_pct': round(((trades_df['equity'].iloc[-1] - 10000) / 10000 * 100), 1),
            'risk_per_trade': risk_per_trade * 100,
            'stop_loss_pips': stop_loss_pips
        }
        
        # Sharpe ratio
        returns = trades_df['pct_return'] / 100
        if len(returns) > 1 and returns.std() > 0:
            stats['sharpe_ratio'] = round((returns.mean() / returns.std()) * np.sqrt(52), 2)
        else:
            stats['sharpe_ratio'] = 0
        
        # Expectancy
        win_rate = stats['win_rate'] / 100
        avg_win = stats['avg_win_pips']
        avg_loss = stats['avg_loss_pips']
        stats['expectancy'] = round((win_rate * avg_win) - ((1 - win_rate) * avg_loss), 1)
        
        return stats
    
    def analyze_thresholds(self, risk_per_trade=0.005, stop_loss_pips=100):
        """Analyze multiple thresholds"""
        thresholds = [-70000, -60000, -50000, -40000, -30000]
        
        results = []
        for threshold in thresholds:
            stats = self.get_strategy_stats(
                threshold=threshold,
                risk_per_trade=risk_per_trade,
                stop_loss_pips=stop_loss_pips
            )
            if stats:
                results.append(stats)
        
        return results
