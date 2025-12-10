"""
REAL BACKTESTER using actual USD/ZAR prices
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import os

class Backtester:
    def __init__(self, cot_data, price_data=None):
        """
        Initialize with COT data AND USD/ZAR price data
        cot_data: COT weekly reports
        price_data: Daily USD/ZAR prices
        """
        self.cot_data = cot_data.copy()
        self.price_data = price_data
        
        # Convert date columns
        if self.price_data is not None and 'Date' in self.price_data.columns:
            self.price_data['date'] = pd.to_datetime(self.price_data['Date'], dayfirst=True)
            self.price_data = self.price_data.sort_values('date')
        
        self.results = {}
    
    def load_price_data(self, filepath="data/usd_zar_historical_data.csv"):
        """Load USD/ZAR historical prices"""
        try:
            df = pd.read_csv(filepath, delimiter='\t')  # Tab-separated based on your sample
            df['date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df = df.sort_values('date')
            
            # Clean price column (remove commas, convert to float)
            if 'Price' in df.columns:
                df['price'] = pd.to_numeric(df['Price'].astype(str).str.replace(',', ''), errors='coerce')
            
            self.price_data = df
            return True
        except Exception as e:
            print(f"Error loading price data: {e}")
            return False
    
    def align_cot_with_prices(self):
        """
        Align COT signals with price data
        COT is released Tuesday (for previous Tuesday)
        We'll assume entry on Wednesday, exit next Tuesday
        """
        if self.price_data is None or self.cot_data is None:
            return None
        
        cot_df = self.cot_data.copy()
        price_df = self.price_data.copy()
        
        # Create aligned dataframe
        aligned_data = []
        
        for i in range(len(cot_df) - 1):  # Skip last one (no future price)
            cot_date = cot_df.iloc[i]['cot_date']
            cot_net = cot_df.iloc[i]['commercial_net']
            
            # Find price on COT date or next day
            price_on_cot = price_df[price_df['date'] >= cot_date].iloc[0]
            entry_price = price_on_cot['price']
            entry_date = price_on_cot['date']
            
            # Find price 7 days later (next COT report)
            exit_date = cot_date + timedelta(days=7)
            price_on_exit = price_df[price_df['date'] >= exit_date]
            
            if len(price_on_exit) > 0:
                exit_price = price_on_exit.iloc[0]['price']
                
                # Calculate return (in pips - USD/ZAR: 1 pip = 0.001)
                price_change = exit_price - entry_price
                pips = price_change * 1000  # Convert to pips
                
                # Percentage return
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
        
        return pd.DataFrame(aligned_data)
    
    def backtest_threshold(self, threshold=-50000):
        """
        Backtest strategy: BUY when commercial_net < threshold
        Hold for 1 week
        """
        aligned_df = self.align_cot_with_prices()
        
        if aligned_df is None or len(aligned_df) == 0:
            return None
        
        # Create signals
        aligned_df['signal'] = (aligned_df['commercial_net'] < threshold).astype(int)
        
        # Filter only trade days
        trades_df = aligned_df[aligned_df['signal'] == 1].copy()
        
        if len(trades_df) == 0:
            return None
        
        # Apply trading costs
        spread_pips = 3  # Typical USD/ZAR spread
        trades_df['net_pips'] = trades_df['pips'] - spread_pips
        
        # Calculate win/loss
        trades_df['win'] = trades_df['net_pips'] > 0
        
        # Equity curve (assuming 1 standard lot = $10 per pip)
        trades_df['trade_profit'] = trades_df['net_pips'] * 10
        trades_df['cumulative_profit'] = trades_df['trade_profit'].cumsum()
        
        return trades_df
    
    def analyze_thresholds(self):
        """Test different threshold values with REAL data"""
        thresholds = [-70000, -60000, -50000, -40000, -30000, -20000, -10000]
        
        analysis = []
        for threshold in thresholds:
            trades_df = self.backtest_threshold(threshold)
            
            if trades_df is not None and len(trades_df) > 5:
                pips = trades_df['net_pips']
                
                analysis.append({
                    'threshold': threshold,
                    'trades': len(trades_df),
                    'win_rate': round((pips > 0).mean() * 100, 1),
                    'avg_pips': round(pips.mean(), 1),
                    'total_pips': round(pips.sum(), 1),
                    'avg_return_pct': round(trades_df['pct_return'].mean(), 3),
                    'max_win': round(pips.max(), 1),
                    'max_loss': round(pips.min(), 1),
                    'profit_factor': round(abs(pips[pips > 0].sum() / pips[pips < 0].sum()), 2) if pips[pips < 0].sum() != 0 else 0
                })
        
        return pd.DataFrame(analysis) if analysis else pd.DataFrame()
    
    def get_strategy_stats(self, threshold=-50000):
        """Get detailed statistics for a specific threshold"""
        trades_df = self.backtest_threshold(threshold)
        
        if trades_df is None or len(trades_df) == 0:
            return None
        
        pips = trades_df['net_pips']
        
        # Calculate drawdown
        equity = 10000 + trades_df['cumulative_profit']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Monthly performance
        trades_df['year_month'] = trades_df['entry_date'].dt.to_period('M')
        monthly = trades_df.groupby('year_month').agg({
            'net_pips': 'sum',
            'pct_return': 'mean'
        }).reset_index()
        
        stats = {
            'total_trades': len(trades_df),
            'winning_trades': len(pips[pips > 0]),
            'losing_trades': len(pips[pips < 0]),
            'win_rate': round((pips > 0).mean() * 100, 1),
            'avg_win': round(pips[pips > 0].mean(), 1) if len(pips[pips > 0]) > 0 else 0,
            'avg_loss': round(abs(pips[pips < 0].mean()), 1) if len(pips[pips < 0]) > 0 else 0,
            'total_pips': round(pips.sum(), 1),
            'max_win': round(pips.max(), 1),
            'max_loss': round(pips.min(), 1),
            'profit_factor': round(abs(pips[pips > 0].sum() / pips[pips < 0].sum()), 2) if pips[pips < 0].sum() != 0 else 0,
            'max_drawdown_pct': round(max_drawdown, 2),
            'avg_return_pct': round(trades_df['pct_return'].mean(), 3),
            'final_equity': round(equity.iloc[-1], 2) if len(equity) > 0 else 10000
        }
        
        # Monthly breakdown
        stats['monthly'] = monthly.to_dict('records')
        
        return stats
    
    def generate_report(self):
        """Generate comprehensive backtest report with REAL data"""
        if self.cot_data is None or len(self.cot_data) == 0:
            return {"error": "No COT data available"}
        
        if self.price_data is None or len(self.price_data) == 0:
            return {"error": "No price data available"}
        
        report = {}
        
        # 1. Data overview
        report['data_overview'] = {
            'total_cot_weeks': len(self.cot_data),
            'total_price_days': len(self.price_data),
            'cot_date_range': f"{self.cot_data['cot_date'].min().date()} to {self.cot_data['cot_date'].max().date()}",
            'price_date_range': f"{self.price_data['date'].min().date()} to {self.price_data['date'].max().date()}",
            'avg_commercial_net': round(self.cot_data['commercial_net'].mean(), 0),
            'min_commercial_net': int(self.cot_data['commercial_net'].min()),
            'max_commercial_net': int(self.cot_data['commercial_net'].max()),
            'avg_usdzar_price': round(self.price_data['price'].mean(), 4),
            'usdzar_volatility': round(self.price_data['price'].pct_change().std() * np.sqrt(252) * 100, 1)  # Annualized %
        }
        
        # 2. Threshold analysis
        threshold_df = self.analyze_thresholds()
        if len(threshold_df) > 0:
            report['threshold_analysis'] = threshold_df.to_dict('records')
            
            # 3. Find best threshold
            if 'total_pips' in threshold_df.columns:
                best_idx = threshold_df['total_pips'].idxmax()
                report['best_threshold'] = threshold_df.loc[best_idx].to_dict()
                
                # 4. Detailed stats for best threshold
                best_threshold = report['best_threshold']['threshold']
                report['detailed_stats'] = self.get_strategy_stats(best_threshold)
        
        # 5. Signal distribution
        self.cot_data['signal_strength'] = pd.cut(
            self.cot_data['commercial_net'],
            bins=[-200000, -60000, -40000, -20000, 0, 20000, 40000, 200000],
            labels=['Extreme Short', 'Strong Short', 'Moderate Short', 'Mild Short',
                   'Mild Long', 'Moderate Long', 'Strong Long']
        )
        
        signal_dist = self.cot_data['signal_strength'].value_counts().to_dict()
        report['signal_distribution'] = signal_dist
        
        return report
