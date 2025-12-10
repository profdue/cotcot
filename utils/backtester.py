"""
REAL BACKTESTER using actual USD/ZAR prices
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import os
import csv

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
        if self.price_data is not None and 'date' in self.price_data.columns:
            self.price_data = self.price_data.sort_values('date')
        
        self.results = {}
    
    def load_price_data(self, filepath="data/usd_zar_historical_data.csv"):
        """
        Load USD/ZAR historical prices with robust error handling
        Handles quoted CSV with BOM encoding
        """
        try:
            # Read the file to inspect first few lines
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                sample = f.read(1000)
                
            # Check if file has BOM and quoted fields
            lines = sample.split('\n')
            
            # Try reading with pandas - handle quoted CSV
            try:
                df = pd.read_csv(
                    filepath,
                    encoding='utf-8-sig',
                    quotechar='"',
                    thousands=',',
                    engine='python'
                )
            except:
                # Try without quotechar
                df = pd.read_csv(
                    filepath,
                    encoding='utf-8-sig',
                    thousands=','
                )
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Find date column (case insensitive)
            date_col = None
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            if date_col is None:
                date_col = df.columns[0]  # Assume first column
            
            # Find price column
            price_col = None
            for col in df.columns:
                if 'price' in col.lower() and col != date_col:
                    price_col = col
                    break
            if price_col is None:
                # Check other common names
                for col in df.columns:
                    if any(x in col.lower() for x in ['close', 'last', 'value']):
                        price_col = col
                        break
            if price_col is None:
                price_col = df.columns[1]  # Assume second column
            
            # Convert and clean
            df['date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            
            # Clean price - remove commas and convert to float
            if df[price_col].dtype == 'object':
                df['price'] = pd.to_numeric(
                    df[price_col].astype(str).str.replace(',', ''), 
                    errors='coerce'
                )
            else:
                df['price'] = df[price_col]
            
            # Remove invalid rows
            df = df.dropna(subset=['date', 'price'])
            df = df.sort_values('date')
            
            # Keep relevant columns
            keep_cols = ['date', 'price']
            for col in ['Open', 'High', 'Low', 'Vol.', 'Change %']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                    keep_cols.append(col)
            
            self.price_data = df[keep_cols]
            return True
            
        except Exception as e:
            print(f"Error loading price data: {str(e)}")
            # Fallback: try manual parsing
            return self._load_price_data_manual(filepath)
    
    def _load_price_data_manual(self, filepath):
        """Manual CSV parsing as fallback"""
        try:
            dates = []
            prices = []
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                # Skip header
                next(reader)
                
                for row in reader:
                    if len(row) < 2:
                        continue
                    
                    try:
                        # Clean the date (remove quotes, trim)
                        date_str = row[0].strip().strip('"')
                        # Clean the price (remove quotes, commas)
                        price_str = row[1].strip().strip('"').replace(',', '')
                        
                        date = pd.to_datetime(date_str, dayfirst=True)
                        price = float(price_str)
                        
                        dates.append(date)
                        prices.append(price)
                    except:
                        continue
            
            if dates:
                df = pd.DataFrame({'date': dates, 'price': prices})
                df = df.dropna()
                df = df.sort_values('date')
                self.price_data = df
                return True
            
            return False
            
        except Exception as e:
            print(f"Manual loading also failed: {e}")
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
        
        # Ensure we have datetime
        cot_df['cot_date'] = pd.to_datetime(cot_df['cot_date'])
        price_df['date'] = pd.to_datetime(price_df['date'])
        
        # Create aligned dataframe
        aligned_data = []
        
        for i in range(len(cot_df) - 1):  # Skip last one (no future price)
            cot_date = cot_df.iloc[i]['cot_date']
            cot_net = cot_df.iloc[i]['commercial_net']
            
            # Find price on or after COT date (entry price)
            price_after_cot = price_df[price_df['date'] >= cot_date]
            if len(price_after_cot) == 0:
                continue
                
            entry_price_data = price_after_cot.iloc[0]
            entry_price = entry_price_data['price']
            entry_date = entry_price_data['date']
            
            # Find price 7 days later (next week)
            exit_date_target = cot_date + timedelta(days=7)
            price_on_exit = price_df[price_df['date'] >= exit_date_target]
            
            if len(price_on_exit) > 0:
                exit_price_data = price_on_exit.iloc[0]
                exit_price = exit_price_data['price']
                exit_date = exit_price_data['date']
                
                # Calculate return
                price_change = exit_price - entry_price
                pips = price_change * 1000  # USD/ZAR: 1 pip = 0.001
                pct_return = (exit_price - entry_price) / entry_price * 100
                
                # Calculate holding days
                holding_days = (exit_date - entry_date).days
                
                aligned_data.append({
                    'cot_date': cot_date,
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'holding_days': holding_days,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'commercial_net': cot_net,
                    'pips': pips,
                    'pct_return': pct_return,
                    'price_change': price_change
                })
        
        if not aligned_data:
            return None
            
        aligned_df = pd.DataFrame(aligned_data)
        
        # Filter out trades with abnormal holding periods (should be ~5-7 days)
        aligned_df = aligned_df[(aligned_df['holding_days'] >= 4) & (aligned_df['holding_days'] <= 10)]
        
        return aligned_df
    
    def backtest_threshold(self, threshold=-50000, capital=10000, risk_per_trade=0.01):
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
        
        # Apply trading costs (3 pip spread for USD/ZAR)
        spread_pips = 3
        trades_df['net_pips'] = trades_df['pips'] - spread_pips
        
        # Calculate position size based on risk
        stop_loss_pips = 50  # 50 pip stop loss
        position_size = (capital * risk_per_trade) / (stop_loss_pips * 10)
        
        # Calculate profit/loss
        trades_df['trade_profit'] = trades_df['net_pips'] * 10 * position_size
        trades_df['cumulative_profit'] = trades_df['trade_profit'].cumsum()
        trades_df['equity'] = capital + trades_df['cumulative_profit']
        
        # Calculate win/loss
        trades_df['win'] = trades_df['net_pips'] > 0
        
        return trades_df
    
    def analyze_thresholds(self):
        """Test different threshold values with REAL data"""
        thresholds = [-70000, -60000, -50000, -40000, -30000, -20000, -10000]
        
        analysis = []
        for threshold in thresholds:
            trades_df = self.backtest_threshold(threshold)
            
            if trades_df is not None and len(trades_df) > 5:
                pips = trades_df['net_pips']
                profits = trades_df['trade_profit']
                
                # Calculate metrics
                win_rate = (pips > 0).mean() * 100
                total_pips = pips.sum()
                avg_pips = pips.mean()
                
                # Profit factor
                winning_pips = pips[pips > 0].sum() if len(pips[pips > 0]) > 0 else 0
                losing_pips = abs(pips[pips < 0].sum()) if len(pips[pips < 0]) > 0 else 1
                profit_factor = winning_pips / losing_pips if losing_pips > 0 else 0
                
                # Drawdown
                equity = trades_df['equity']
                peak = equity.expanding().max()
                drawdown = (equity - peak) / peak
                max_dd = drawdown.min() * 100
                
                analysis.append({
                    'threshold': threshold,
                    'trades': len(trades_df),
                    'win_rate': round(win_rate, 1),
                    'avg_pips': round(avg_pips, 1),
                    'total_pips': round(total_pips, 1),
                    'total_profit': round(profits.sum(), 0),
                    'avg_return_pct': round(trades_df['pct_return'].mean(), 3),
                    'max_win_pips': round(pips.max(), 1),
                    'max_loss_pips': round(pips.min(), 1),
                    'profit_factor': round(profit_factor, 2),
                    'max_drawdown_pct': round(max_dd, 2)
                })
        
        return pd.DataFrame(analysis) if analysis else pd.DataFrame()
    
    def get_strategy_stats(self, threshold=-50000):
        """Get detailed statistics for a specific threshold"""
        trades_df = self.backtest_threshold(threshold)
        
        if trades_df is None or len(trades_df) == 0:
            return None
        
        pips = trades_df['net_pips']
        profits = trades_df['trade_profit']
        
        # Calculate drawdown
        equity = trades_df['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Sharpe ratio (annualized)
        returns = trades_df['pct_return'] / 100
        if len(returns) > 1:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(52)  # Weekly to annual
        else:
            sharpe = 0
        
        # Monthly performance
        trades_df['year_month'] = trades_df['entry_date'].dt.to_period('M')
        monthly = trades_df.groupby('year_month').agg({
            'net_pips': 'sum',
            'pct_return': 'mean',
            'trade_profit': 'sum'
        }).reset_index()
        
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
            'sharpe_ratio': round(sharpe, 2),
            'final_equity': round(equity.iloc[-1], 2) if len(equity) > 0 else 10000,
            'roi_pct': round(((equity.iloc[-1] - 10000) / 10000 * 100), 1) if len(equity) > 0 else 0
        }
        
        # Monthly breakdown
        stats['monthly'] = monthly.to_dict('records')
        
        # Trade-by-trade data for charts
        stats['trades_data'] = trades_df[['entry_date', 'net_pips', 'pct_return', 'equity']].to_dict('records')
        
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
            'usdzar_range': f"{self.price_data['price'].min():.4f} to {self.price_data['price'].max():.4f}",
            'current_usdzar': round(self.price_data['price'].iloc[-1], 4) if len(self.price_data) > 0 else 0
        }
        
        # 2. Threshold analysis
        threshold_df = self.analyze_thresholds()
        if len(threshold_df) > 0:
            report['threshold_analysis'] = threshold_df.to_dict('records')
            
            # 3. Find best threshold based on profit factor
            if 'profit_factor' in threshold_df.columns:
                # Filter for reasonable number of trades
                valid_thresholds = threshold_df[threshold_df['trades'] >= 10]
                if len(valid_thresholds) > 0:
                    best_idx = valid_thresholds['profit_factor'].idxmax()
                    report['best_threshold'] = valid_thresholds.loc[best_idx].to_dict()
                    
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
        
        signal_dist = self.cot_data['signal_strength'].value_counts().sort_index().to_dict()
        report['signal_distribution'] = signal_dist
        
        # 6. Data quality info
        aligned_df = self.align_cot_with_prices()
        if aligned_df is not None:
            report['alignment_info'] = {
                'aligned_trades': len(aligned_df),
                'avg_holding_days': round(aligned_df['holding_days'].mean(), 1),
                'successful_alignment_pct': round(len(aligned_df) / len(self.cot_data) * 100, 1)
            }
        
        return report
