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
        Load USD/ZAR historical prices - SIMPLIFIED VERSION
        """
        try:
            # Method 1: Direct pandas read with proper parameters
            try:
                df = pd.read_csv(
                    filepath,
                    encoding='utf-8-sig',
                    quotechar='"',
                    thousands=',',
                    engine='python'
                )
            except Exception as e1:
                # Method 2: Try without quotechar
                try:
                    df = pd.read_csv(
                        filepath,
                        encoding='utf-8-sig',
                        thousands=','
                    )
                except Exception as e2:
                    # Method 3: Try manual parsing
                    df = self._manual_csv_parse(filepath)
                    if df is None:
                        raise Exception(f"Failed to read CSV: {e1}, {e2}")
            
            # Debug: Show what we got
            print(f"Loaded columns: {df.columns.tolist()}")
            print(f"First few rows:\n{df.head()}")
            
            # Clean column names
            df.columns = [col.strip().replace('"', '') for col in df.columns]
            
            # Find date column
            date_col = None
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            if date_col is None:
                # Try common column names
                for col in df.columns:
                    if any(x in col.lower() for x in ['date', 'time', 'day']):
                        date_col = col
                        break
            if date_col is None:
                date_col = df.columns[0]
            
            # Find price column
            price_col = None
            for col in df.columns:
                if 'price' in col.lower() and col != date_col:
                    price_col = col
                    break
            if price_col is None:
                for col in df.columns:
                    if any(x in col.lower() for x in ['price', 'close', 'last', 'value']):
                        price_col = col
                        break
            if price_col is None:
                price_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            
            print(f"Using date column: {date_col}, price column: {price_col}")
            
            # Convert date
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
            df = df.dropna(subset=['date', 'price'])
            df = df.sort_values('date')
            
            # Keep only essential columns
            keep_cols = ['date', 'price']
            for col in ['Open', 'High', 'Low', 'Vol.', 'Change %', 'Vol']:
                if col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                        keep_cols.append(col)
                    except:
                        pass
            
            self.price_data = df[keep_cols]
            print(f"Successfully loaded {len(self.price_data)} price records")
            return True
            
        except Exception as e:
            print(f"Error loading price data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _manual_csv_parse(self, filepath):
        """Manual CSV parsing as fallback"""
        try:
            data = []
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                lines = content.split('\n')
                
                # Extract header
                if lines:
                    header_line = lines[0].strip()
                    # Remove quotes and split
                    headers = [h.strip('"') for h in header_line.split(',')]
                    
                    # Parse data rows
                    for line in lines[1:]:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Remove quotes and split
                        values = []
                        in_quotes = False
                        current_value = []
                        
                        for char in line:
                            if char == '"':
                                in_quotes = not in_quotes
                            elif char == ',' and not in_quotes:
                                values.append(''.join(current_value).strip('"'))
                                current_value = []
                            else:
                                current_value.append(char)
                        
                        if current_value:
                            values.append(''.join(current_value).strip('"'))
                        
                        if len(values) >= 2:
                            data.append(values)
            
            if data and headers:
                df = pd.DataFrame(data, columns=headers[:len(data[0])])
                return df
            
        except Exception as e:
            print(f"Manual parsing failed: {e}")
        
        return None
    
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
                print("No data aligned")
                return None
            
            aligned_df = pd.DataFrame(aligned_data)
            
            # Filter reasonable holding periods
            aligned_df = aligned_df[
                (aligned_df['holding_days'] >= 4) & 
                (aligned_df['holding_days'] <= 10)
            ]
            
            print(f"Aligned {len(aligned_df)} trades")
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
            print(f"No aligned data for threshold {threshold}")
            return None
        
        # Create signals
        aligned_df['signal'] = (aligned_df['commercial_net'] < threshold).astype(int)
        
        # Filter only trade days
        trades_df = aligned_df[aligned_df['signal'] == 1].copy()
        
        if len(trades_df) == 0:
            print(f"No signals for threshold {threshold}")
            return None
        
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
        
        print(f"Backtest complete: {len(trades_df)} trades for threshold {threshold}")
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
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        if self.cot_data is None or len(self.cot_data) == 0:
            return {"error": "No COT data available"}
        
        if self.price_data is None or len(self.price_data) == 0:
            return {"error": "No price data available"}
        
        report = {}
        
        try:
            # Data overview
            report['data_overview'] = {
                'total_cot_weeks': len(self.cot_data),
                'total_price_days': len(self.price_data),
                'cot_date_range': f"{self.cot_data['cot_date'].min().date()} to {self.cot_data['cot_date'].max().date()}",
                'price_date_range': f"{self.price_data['date'].min().date()} to {self.price_data['date'].max().date()}",
                'avg_commercial_net': round(self.cot_data['commercial_net'].mean(), 0),
                'min_commercial_net': int(self.cot_data['commercial_net'].min()),
                'max_commercial_net': int(self.cot_data['commercial_net'].max()),
                'avg_usdzar_price': round(self.price_data['price'].mean(), 4),
                'current_usdzar': round(self.price_data['price'].iloc[-1], 4)
            }
            
            # Threshold analysis
            threshold_df = self.analyze_thresholds()
            if len(threshold_df) > 0:
                report['threshold_analysis'] = threshold_df.to_dict('records')
                
                # Find best threshold
                if 'profit_factor' in threshold_df.columns:
                    valid_df = threshold_df[threshold_df['trades'] >= 10]
                    if len(valid_df) > 0:
                        best_idx = valid_df['profit_factor'].idxmax()
                        report['best_threshold'] = valid_df.loc[best_idx].to_dict()
                        
                        # Detailed stats
                        best_threshold = report['best_threshold']['threshold']
                        report['detailed_stats'] = self.get_strategy_stats(best_threshold)
            
            # Signal distribution
            self.cot_data['signal_strength'] = pd.cut(
                self.cot_data['commercial_net'],
                bins=[-200000, -60000, -40000, -20000, 0, 20000, 40000, 200000],
                labels=['Extreme Short', 'Strong Short', 'Moderate Short', 'Mild Short',
                       'Mild Long', 'Moderate Long', 'Strong Long']
            )
            
            signal_dist = self.cot_data['signal_strength'].value_counts().sort_index().to_dict()
            report['signal_distribution'] = signal_dist
            
        except Exception as e:
            report['error'] = f"Error generating report: {str(e)}"
        
        return report
