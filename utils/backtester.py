"""
REAL BACKTESTER using actual USD/ZAR prices
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import os
import csv

class Backtester:
    def __init__(self, cot_data=None, price_data=None):
        """
        Initialize with COT data AND USD/ZAR price data
        """
        self.cot_data = cot_data.copy() if cot_data is not None else None
        self.price_data = price_data.copy() if price_data is not None else None
        self.results = {}
    
    def load_price_data(self, filepath="data/usd_zar_historical_data.csv"):
        """
        Load USD/ZAR historical prices - FIXED for DD/MM/YYYY dates
        """
        try:
            print(f"Loading price data from {filepath}...")
            
            # Method 1: Read with pandas, handle DD/MM/YYYY
            df = pd.read_csv(
                filepath,
                encoding='utf-8-sig',
                quotechar='"',
                thousands=',',
                engine='python'
            )
            
            # Clean column names
            df.columns = [col.strip().replace('"', '') for col in df.columns]
            print(f"Columns found: {df.columns.tolist()}")
            
            # Find date column
            date_col = None
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            if date_col is None:
                date_col = 'Date' if 'Date' in df.columns else df.columns[0]
            
            # Find price column
            price_col = None
            for col in df.columns:
                if 'price' in col.lower() and col != date_col:
                    price_col = col
                    break
            if price_col is None:
                price_col = 'Price' if 'Price' in df.columns else df.columns[1]
            
            print(f"Using date column: '{date_col}', price column: '{price_col}'")
            
            # CRITICAL FIX: Parse DD/MM/YYYY dates properly
            def parse_date(date_str):
                try:
                    # Remove any quotes and whitespace
                    date_str = str(date_str).strip().strip('"')
                    # Split by /
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        # Handle 2-digit year
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        return pd.Timestamp(f"{year}-{month}-{day}")
                except:
                    pass
                return pd.NaT
            
            # Apply custom date parser
            df['date'] = df[date_col].apply(parse_date)
            
            # Alternative: try pandas parser with dayfirst=True
            if df['date'].isna().all():
                print("Custom parser failed, trying pandas with dayfirst=True...")
                df['date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            
            # Convert price
            if df[price_col].dtype == 'object':
                df['price'] = pd.to_numeric(
                    df[price_col].astype(str).str.replace(',', ''), 
                    errors='coerce'
                )
            else:
                df['price'] = df[price_col]
            
            # Remove invalid rows
            initial_count = len(df)
            df = df.dropna(subset=['date', 'price'])
            df = df.sort_values('date')
            
            print(f"Loaded {len(df)} valid records (dropped {initial_count - len(df)} invalid)")
            print(f"Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"Price range: {df['price'].min():.4f} to {df['price'].max():.4f}")
            
            self.price_data = df[['date', 'price']]
            return True
            
        except Exception as e:
            print(f"Error loading price data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def align_cot_with_prices(self):
        """
        Align COT signals with price data
        """
        if self.price_data is None or self.cot_data is None:
            print("Cannot align: Missing price or COT data")
            return None
        
        try:
            cot_df = self.cot_data.copy()
            price_df = self.price_data.copy()
            
            print(f"COT date range: {cot_df['cot_date'].min()} to {cot_df['cot_date'].max()}")
            print(f"Price date range: {price_df['date'].min()} to {price_df['date'].max()}")
            
            # Ensure datetime
            cot_df['cot_date'] = pd.to_datetime(cot_df['cot_date'])
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            # Sort both
            cot_df = cot_df.sort_values('cot_date')
            price_df = price_df.sort_values('date')
            
            aligned_data = []
            
            for i in range(len(cot_df) - 1):
                cot_date = cot_df.iloc[i]['cot_date']
                cot_net = cot_df.iloc[i]['commercial_net']
                
                # Find entry price (next trading day after COT date)
                entry_mask = price_df['date'] > cot_date
                if not entry_mask.any():
                    continue
                    
                entry_row = price_df[entry_mask].iloc[0]
                entry_date = entry_row['date']
                entry_price = entry_row['price']
                
                # Find exit price (approximately 1 week later)
                # Look for price 5-7 business days later
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
                print("No data aligned - check date ranges")
                return None
            
            aligned_df = pd.DataFrame(aligned_data)
            
            print(f"Successfully aligned {len(aligned_df)} trades")
            print(f"Average holding days: {aligned_df['holding_days'].mean():.1f}")
            
            return aligned_df
            
        except Exception as e:
            print(f"Error in align_cot_with_prices: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def backtest_threshold(self, threshold=-50000, capital=10000, risk_per_trade=0.01):
        """
        Backtest strategy: BUY when commercial_net < threshold
        """
        aligned_df = self.align_cot_with_prices()
        
        if aligned_df is None or len(aligned_df) == 0:
            print(f"No aligned data for backtesting")
            return None
        
        # Create signals
        aligned_df['signal'] = (aligned_df['commercial_net'] < threshold).astype(int)
        
        # Filter only trade days
        trades_df = aligned_df[aligned_df['signal'] == 1].copy()
        
        if len(trades_df) == 0:
            print(f"No signals for threshold {threshold}")
            return None
        
        print(f"Found {len(trades_df)} trades for threshold {threshold}")
        
        # Apply trading costs
        spread_pips = 3
        trades_df['net_pips'] = trades_df['pips'] - spread_pips
        
        # Position sizing
        stop_loss_pips = 50
        position_size = (capital * risk_per_trade) / (stop_loss_pips * 10)
        
        # Calculate profit/loss
        trades_df['trade_profit'] = trades_df['net_pips'] * 10 * position_size
        trades_df['cumulative_profit'] = trades_df['trade_profit'].cumsum()
        trades_df['equity'] = capital + trades_df['cumulative_profit']
        trades_df['win'] = trades_df['net_pips'] > 0
        
        return trades_df
    
    def analyze_thresholds(self):
        """Test different threshold values"""
        thresholds = [-70000, -60000, -50000, -40000, -30000, -20000, -10000]
        
        analysis = []
        for threshold in thresholds:
            trades_df = self.backtest_threshold(threshold)
            
            if trades_df is not None and len(trades_df) >= 5:
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
        """Get detailed statistics"""
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
