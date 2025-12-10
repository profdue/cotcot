"""
SIMPLE BACKTESTER - Find basic edge in COT data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class SimpleBacktester:
    def __init__(self, data):
        self.data = data
        self.results = {}
        
    def analyze_thresholds(self):
        """Test different commercial net thresholds"""
        thresholds = [-70000, -60000, -50000, -40000, -30000, -20000]
        
        results = []
        for threshold in thresholds:
            # BUY when commercials are VERY short (< threshold)
            buy_signals = self.data[self.data['commercial_net'] < threshold]
            
            if len(buy_signals) > 10:  # Need enough samples
                avg_pips = buy_signals['pips_change'].mean()
                win_rate = (len(buy_signals[buy_signals['pips_change'] > 0]) / len(buy_signals)) * 100
                total_trades = len(buy_signals)
                
                results.append({
                    'threshold': threshold,
                    'trades': total_trades,
                    'avg_pips': avg_pips,
                    'win_rate': win_rate,
                    'total_pips': avg_pips * total_trades
                })
        
        return pd.DataFrame(results)
    
    def analyze_holding_periods(self, threshold=-50000):
        """Test different holding periods"""
        # We'll simulate different exit days (1-5 days after entry)
        holding_days = [1, 2, 3, 4, 5]
        
        results = []
        for days in holding_days:
            # For each COT signal, calculate pips after X days
            day_pips = []
            
            for _, row in self.data.iterrows():
                if row['commercial_net'] < threshold:
                    # Get price X days after entry
                    # In real version, would need daily price data
                    # For now, approximate: assume linear progression
                    weekly_pips = row['pips_change']
                    daily_avg = weekly_pips / 5  # Assume equal daily moves
                    day_pips.append(daily_avg * days)
            
            if day_pips:
                results.append({
                    'hold_days': days,
                    'avg_pips': np.mean(day_pips),
                    'win_rate': (np.sum(np.array(day_pips) > 0) / len(day_pips)) * 100,
                    'trades': len(day_pips)
                })
        
        return pd.DataFrame(results)
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        if self.data is None or len(self.data) == 0:
            return {"error": "No data available"}
        
        report = {}
        
        # 1. Overall stats
        report['overall'] = {
            'total_weeks': len(self.data),
            'avg_weekly_pips': self.data['pips_change'].mean(),
            'positive_weeks': len(self.data[self.data['pips_change'] > 0]),
            'positive_rate': (len(self.data[self.data['pips_change'] > 0]) / len(self.data)) * 100,
            'std_dev': self.data['pips_change'].std()
        }
        
        # 2. Threshold analysis
        threshold_df = self.analyze_thresholds()
        report['thresholds'] = threshold_df.to_dict('records')
        
        # 3. Find best threshold
        if len(threshold_df) > 0:
            best_idx = threshold_df['total_pips'].idxmax()
            report['best_threshold'] = threshold_df.loc[best_idx].to_dict()
        
        # 4. By year analysis
        self.data['year'] = self.data['cot_date'].dt.year
        yearly_stats = self.data.groupby('year').agg({
            'pips_change': ['mean', 'count', lambda x: (x > 0).mean() * 100]
        }).round(2)
        yearly_stats.columns = ['avg_pips', 'weeks', 'win_rate']
        report['yearly'] = yearly_stats.to_dict('index')
        
        # 5. Signal strength buckets
        self.data['signal_strength'] = pd.cut(
            self.data['commercial_net'],
            bins=[-100000, -60000, -40000, -20000, 0, 20000, 40000, 100000],
            labels=['Extreme Short', 'Strong Short', 'Moderate Short', 'Mild Short',
                   'Mild Long', 'Moderate Long', 'Strong Long']
        )
        
        bucket_stats = self.data.groupby('signal_strength').agg({
            'pips_change': ['mean', 'count', lambda x: (x > 0).mean() * 100]
        }).round(2)
        bucket_stats.columns = ['avg_pips', 'weeks', 'win_rate']
        report['signal_buckets'] = bucket_stats.to_dict('index')
        
        return report
    
    def plot_equity_curve(self, threshold=-50000, initial_capital=100):
        """Plot equity curve for a given strategy"""
        # Filter signals
        signals = self.data[self.data['commercial_net'] < threshold].copy()
        signals = signals.sort_values('entry_date')
        
        if len(signals) == 0:
            return None
        
        # Calculate equity curve
        # Assume 0.01 lots = $0.10 per pip (approximate for USD/ZAR)
        pip_value = 0.10
        signals['trade_pnl'] = signals['pips_change'] * pip_value
        signals['cumulative_pnl'] = signals['trade_pnl'].cumsum()
        signals['equity'] = initial_capital + signals['cumulative_pnl']
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Equity curve
        ax1.plot(signals['entry_date'], signals['equity'], linewidth=2)
        ax1.set_title(f'Equity Curve (Threshold: {threshold})')
        ax1.set_ylabel('Account Balance ($)')
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        signals['peak'] = signals['equity'].cummax()
        signals['drawdown'] = (signals['equity'] - signals['peak']) / signals['peak'] * 100
        ax2.fill_between(signals['entry_date'], 0, signals['drawdown'], color='red', alpha=0.3)
        ax2.plot(signals['entry_date'], signals['drawdown'], color='red', linewidth=1)
        ax2.set_title('Drawdown (%)')
        ax2.set_ylabel('Drawdown %')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
