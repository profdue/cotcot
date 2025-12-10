"""
REAL BACKTESTER using actual USD/ZAR prices
FIXED VERSION: Handles None data properly
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
        """
        self.cot_data = cot_data.copy() if cot_data is not None else None
        self.price_data = price_data.copy() if price_data is not None else None
        
        if self.price_data is not None and 'date' in self.price_data.columns:
            self.price_data = self.price_data.sort_values('date')
        
        self.results = {}
    
    def load_price_data_from_file(self, filepath="data/usd_zar_historical_data.csv"):
        """
        Load USD/ZAR historical prices directly from file
        Returns DataFrame if successful, None otherwise
        """
        try:
            # First, read the raw file to see format
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read(5000)
                lines = content.split('\n')
                
            # Try different reading methods
            price_df = None
            
            # Method 1: Standard CSV with quotes (your format)
            try:
                price_df = pd.read_csv(
                    filepath,
                    encoding='utf-8-sig',
                    quotechar='"',
                    thousands=',',
                    engine='python'
                )
                print(f"Method 1 successful. Columns: {price_df.columns.tolist()}")
            except Exception as e1:
                print(f"Method 1 failed: {str(e1)[:100]}")
                
                # Method 2: Try without engine specification
                try:
                    price_df = pd.read_csv(
                        filepath,
                        encoding='utf-8-sig',
                        quotechar='"',
                        thousands=','
                    )
                    print(f"Method 2 successful. Columns: {price_df.columns.tolist()}")
                except Exception as e2:
                    print(f"Method 2 failed: {str(e2)[:100]}")
                    
                    # Method 3: Manual parsing
                    try:
                        price_df = self._manual_csv_parse(filepath)
                        print(f"Method 3 (manual) successful")
                    except Exception as e3:
                        print(f"All methods failed: {str(e3)[:100]}")
                        return None
            
            if price_df is None or len(price_df) == 0:
                return None
            
            # Clean column names
            price_df.columns = price_df.columns.str.strip()
            price_df.columns = price_df.columns.str.replace(r'[^\x00-\x7F]+', '', regex=True)
            
            # Find and process date column
            date_col = self._find_date_column(price_df)
            if date_col is None:
                print("Could not find date column")
                return None
            
            price_df['date'] = pd.to_datetime(price_df[date_col], dayfirst=True, errors='coerce')
            
            # Find and process price column
            price_col = self._find_price_column(price_df, date_col)
            if price_col is None:
                print("Could not find price column")
                return None
            
            # Convert price to numeric
            if price_df[price_col].dtype == 'object':
                price_df['price'] = pd.to_numeric(
                    price_df[price_col].astype(str).str.replace(',', ''), 
                    errors='coerce'
                )
            else:
                price_df['price'] = price_df[price_col]
            
            # Clean up
            price_df = price_df.dropna(subset=['date', 'price'])
            price_df = price_df.sort_values('date')
            
            # Keep only essential columns
            keep_cols = ['date', 'price']
            for col in ['Open', 'High', 'Low', 'Vol.', 'Change %', 'Change']:
                if col in price_df.columns:
                    try:
                        price_df[col] = pd.to_numeric(
                            price_df[col].astype(str).str.replace(',', ''), 
                            errors='coerce'
                        )
                        keep_cols.append(col)
                    except:
                        pass
            
            result_df = price_df[keep_cols].copy()
            print(f"Successfully loaded {len(result_df)} price records")
            print(f"Date range: {result_df['date'].min()} to {result_df['date'].max()}")
            
            return result_df
            
        except Exception as e:
            print(f"Error in load_price_data_from_file: {str(e)}")
            return None
    
    def _manual_csv_parse(self, filepath):
        """Manual CSV parsing as fallback"""
        dates = []
        prices = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            
            # Skip header
            try:
                header = next(reader)
                print(f"CSV Header: {header}")
            except:
                header = []
            
            for row_num, row in enumerate(reader, 1):
                if len(row) < 2:
                    continue
                
                try:
                    # Clean and parse
                    date_str = row[0].strip().strip('"\'')
                    price_str = row[1].strip().strip('"\'').replace(',', '')
                    
                    # Try different date formats
                    date = None
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y']:
                        try:
                            date = pd.to_datetime(date_str, format=fmt)
                            break
                        except:
                            continue
                    
                    if date is None:
                        # Last resort: let pandas guess
                        date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
                    
                    price = float(price_str)
                    
                    if pd.notna(date):
                        dates.append(date)
                        prices.append(price)
                        
                except Exception as e:
                    if row_num <= 5:  # Only show errors for first few rows
                        print(f"Row {row_num} error: {str(e)[:50]}")
                    continue
        
        if dates:
            df = pd.DataFrame({'date': dates, 'price': prices})
            df = df.dropna()
            return df
        
        return None
    
    def _find_date_column(self, df):
        """Find date column in dataframe"""
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['date', 'time', 'day', 'timestamp']):
                return col
        
        # Check first column if it looks like dates
        first_col = df.columns[0]
        sample = df[first_col].dropna().iloc[0] if len(df) > 0 else ''
        if isinstance(sample, str) and any(x in sample for x in ['/', '-', '202', '201']):
            return first_col
        
        return None
    
    def _find_price_column(self, df, exclude_col):
        """Find price column in dataframe"""
        for col in df.columns:
            if col == exclude_col:
                continue
            col_lower = col.lower()
            if any(x in col_lower for x in ['price', 'close', 'last', 'value', 'rate']):
                return col
        
        # Check second column
        if len(df.columns) > 1 and df.columns[1] != exclude_col:
            return df.columns[1]
        
        return None
    
    def set_price_data(self, price_data):
        """Set price data after initialization"""
        if price_data is not None:
            self.price_data = price_data.copy()
            if 'date' in self.price_data.columns:
                self.price_data = self.price_data.sort_values('date')
            return True
        return False
    
    def align_cot_with_prices(self):
        """
        Align COT signals with price data
        Returns None if data is missing or alignment fails
        """
        if self.price_data is None or self.cot_data is None:
            print("Missing data for alignment")
            return None
        
        try:
            cot_df = self.cot_data.copy()
            price_df = self.price_data.copy()
            
            # Ensure we have datetime
            cot_df['cot_date'] = pd.to_datetime(cot_df['cot_date'])
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            # Create aligned dataframe
            aligned_data = []
            
            for i in range(len(cot_df) - 1):  # Skip last one
                cot_date = cot_df.iloc[i]['cot_date']
                cot_net = cot_df.iloc[i]['commercial_net']
                
                # Find entry price (next trading day after COT)
                price_after_cot = price_df[price_df['date'] > cot_date]
                if len(price_after_cot) == 0:
                    continue
                
                entry_price_data = price_after_cot.iloc[0]
                entry_price = entry_price_data['price']
                entry_date = entry_price_data['date']
                
                # Find exit price (7 days later)
                exit_date_target = cot_date + timedelta(days=7)
                price_on_exit = price_df[price_df['date'] >= exit_date_target]
                
                if len(price_on_exit) > 0:
                    exit_price_data = price_on_exit.iloc[0]
                    exit_price = exit_price_data['price']
                    exit_date = exit_price_data['date']
                    
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
                        'price_change': price_change
                    })
            
            if not aligned_data:
                print("No data aligned")
                return None
            
            aligned_df = pd.DataFrame(aligned_data)
            print(f"Successfully aligned {len(aligned_df)} trades")
            return aligned_df
            
        except Exception as e:
            print(f"Error in align_cot_with_prices: {str(e)}")
            return None
    
    def backtest_threshold(self, threshold=-50000, capital=10000, risk_per_trade=0.01):
        """
        Backtest strategy: BUY when commercial_net < threshold
        """
        aligned_df = self.align_cot_with_prices()
        
        if aligned_df is None or len(aligned_df) == 0:
            print(f"No aligned data for threshold {threshold}")
            return None
        
        # Create signals
        aligned_df['signal'] = (aligned_df['commercial_net'] < threshold).astype(int)
        
        # Filter only trade days
        trades_df = aligned_df[aligned_df['signal'] == 1].copy()
        
        if len(trades_df) == 0:
            print(f"No signals for threshold {threshold}")
            return None
        
        print(f"Found {len(trades_df)} trades for threshold {threshold}")
        
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
        if self.price_data is None or self.cot_data is None:
            print("Missing data for threshold analysis")
            return pd.DataFrame()
        
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
        
        # Sharpe ratio
        returns = trades_df['pct_return'] / 100
        if len(returns) > 1 and returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(52)
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
        
        return stats
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
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
            
            # Find best threshold
            if 'profit_factor' in threshold_df.columns:
                valid_thresholds = threshold_df[threshold_df['trades'] >= 10]
                if len(valid_thresholds) > 0:
                    best_idx = valid_thresholds['profit_factor'].idxmax()
                    report['best_threshold'] = valid_thresholds.loc[best_idx].to_dict()
                    
                    # Detailed stats
                    best_threshold = report['best_threshold']['threshold']
                    report['detailed_stats'] = self.get_strategy_stats(best_threshold)
        
        # 3. Signal distribution
        self.cot_data['signal_strength'] = pd.cut(
            self.cot_data['commercial_net'],
            bins=[-200000, -60000, -40000, -20000, 0, 20000, 40000, 200000],
            labels=['Extreme Short', 'Strong Short', 'Moderate Short', 'Mild Short',
                   'Mild Long', 'Moderate Long', 'Strong Long']
        )
        
        signal_dist = self.cot_data['signal_strength'].value_counts().sort_index().to_dict()
        report['signal_distribution'] = signal_dist
        
        return report
