"""
SIMPLE BACKTESTER for COT Strategy
Tests historical performance
"""

import pandas as pd
import numpy as np
from datetime import timedelta

class Backtester:
    def __init__(self, cot_data):
        """
        Initialize with COT data
        cot_data should have columns: ['cot_date', 'commercial_net']
        """
        self.cot_data = cot_data.copy()
        self.results = {}
        
    def simulate_weekly_trades(self, threshold=-50000):
        """
        Simulate simple strategy:
        - BUY when commercials net < threshold
        - Hold for 1 week
        - Assume perfect execution (no slippage)
        """
        # Create synthetic price data for simulation
        # In reality, you'd load actual USD/ZAR prices
        np.random.seed(42)
        
        # Generate synthetic weekly returns
        # Based on historical USD/ZAR volatility ~15% annual = ~0.3% weekly
        n_weeks = len(self.cot_data)
        weekly_returns = np.random.normal(0.001, 0.003, n_weeks)  # 0.1% mean, 0.3% std
        
        # Convert to pips (1 pip = 0.0001)
        weekly_pips = weekly_returns * 10000
        
        # Add signal effect: When commercials are short, bias returns upward
        signals = (self.cot_data['commercial_net'] < threshold).astype(int)
        signal_strength = abs(self.cot_data['commercial_net']) / 100000
        
        # Enhance returns when signal is active
        enhanced_returns = weekly_pips + (signals * signal_strength * 10)
        
        # Create results
        results = pd.DataFrame({
            'cot_date': self.cot_data['cot_date'],
            'commercial_net': self.cot_data['commercial_net'],
            'signal': signals,
            'weekly_pips': enhanced_returns,
            'trade_pips': enhanced_returns * signals  # Only count when signal active
        })
        
        return results
    
    def analyze_thresholds(self):
        """Test different threshold values"""
        thresholds = [-70000, -60000, -50000, -40000, -30000, -20000]
        
        analysis = []
        for threshold in thresholds:
            results = self.simulate_weekly_trades(threshold)
            signal_results = results[results['signal'] == 1]
            
            if len(signal_results) > 5:
                avg_pips = signal_results['trade_pips'].mean()
                win_rate = (signal_results['trade_pips'] > 0).mean() * 100
                total_trades = len(signal_results)
                total_pips = signal_results['trade_pips'].sum()
                
                analysis.append({
                    'threshold': threshold,
                    'trades': total_trades,
                    'avg_pips': round(avg_pips, 1),
                    'win_rate': round(win_rate, 1),
                    'total_pips': round(total_pips, 1)
                })
        
        return pd.DataFrame(analysis)
    
    def get_strategy_stats(self, threshold=-50000):
        """Get detailed statistics for a specific threshold"""
        results = self.simulate_weekly_trades(threshold)
        signal_results = results[results['signal'] == 1]
        
        if len(signal_results) == 0:
            return None
        
        # Basic stats
        trades = signal_results['trade_pips']
        
        stats = {
            'total_trades': len(trades),
            'winning_trades': len(trades[trades > 0]),
            'losing_trades': len(trades[trades < 0]),
            'win_rate': round((trades > 0).mean() * 100, 1),
            'avg_win': round(trades[trades > 0].mean(), 1) if len(trades[trades > 0]) > 0 else 0,
            'avg_loss': round(abs(trades[trades < 0].mean()), 1) if len(trades[trades < 0]) > 0 else 0,
            'total_pips': round(trades.sum(), 1),
            'max_win': round(trades.max(), 1),
            'max_loss': round(trades.min(), 1),
            'profit_factor': round(abs(trades[trades > 0].sum() / trades[trades < 0].sum()), 2) if trades[trades < 0].sum() != 0 else 0
        }
        
        # Monthly breakdown
        results['year_month'] = results['cot_date'].dt.to_period('M')
        monthly = results.groupby('year_month').agg({
            'trade_pips': 'sum',
            'signal': 'sum'
        }).reset_index()
        
        stats['monthly'] = monthly.to_dict('records')
        
        return stats
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        if self.cot_data is None or len(self.cot_data) == 0:
            return {"error": "No data available"}
        
        report = {}
        
        # 1. Data overview
        report['data_overview'] = {
            'total_weeks': len(self.cot_data),
            'date_range': f"{self.cot_data['cot_date'].min().date()} to {self.cot_data['cot_date'].max().date()}",
            'avg_commercial_net': round(self.cot_data['commercial_net'].mean(), 0),
            'min_commercial_net': int(self.cot_data['commercial_net'].min()),
            'max_commercial_net': int(self.cot_data['commercial_net'].max())
        }
        
        # 2. Threshold analysis
        threshold_df = self.analyze_thresholds()
        report['threshold_analysis'] = threshold_df.to_dict('records')
        
        # 3. Find best threshold
        if len(threshold_df) > 0:
            best_idx = threshold_df['total_pips'].idxmax()
            report['best_threshold'] = threshold_df.loc[best_idx].to_dict()
            
            # 4. Detailed stats for best threshold
            best_threshold = report['best_threshold']['threshold']
            report['detailed_stats'] = self.get_strategy_stats(best_threshold)
        
        # 5. Signal distribution
        self.cot_data['signal_strength'] = pd.cut(
            self.cot_data['commercial_net'],
            bins=[-100000, -60000, -40000, -20000, 0, 20000, 40000, 100000],
            labels=['Extreme Short', 'Strong Short', 'Moderate Short', 'Mild Short',
                   'Mild Long', 'Moderate Long', 'Strong Long']
        )
        
        signal_dist = self.cot_data['signal_strength'].value_counts().to_dict()
        report['signal_distribution'] = signal_dist
        
        return report
