"""
COT + PRICE DATA MERGER
Creates the foundation for backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf  # For getting price data

class DataEngine:
    def __init__(self):
        self.cot_data = None
        self.price_data = None
        self.merged_data = None
        
    def load_cot_data(self, data_paths):
        """Load and clean COT data from CSV files"""
        dfs = []
        for path in data_paths:
            try:
                df = pd.read_csv(path)
                
                # Filter for REGULAR GOLD only (not MICRO)
                if 'Market_and_Exchange_Names' in df.columns:
                    df = df[~df['Market_and_Exchange_Names'].str.contains('MICRO', na=False)]
                
                # Extract date
                if 'Report_Date_as_MM_DD_YYYY' in df.columns:
                    df['cot_date'] = pd.to_datetime(df['Report_Date_as_MM_DD_YYYY'])
                elif 'As_of_Date_In_Form_YYMMDD' in df.columns:
                    # Convert YYMMDD to date
                    df['cot_date'] = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
                
                # Extract commercial positions
                df['commercial_long'] = df.get('Prod_Merc_Positions_Long_ALL', 0)
                df['commercial_short'] = df.get('Prod_Merc_Positions_Short_ALL', 0)
                df['commercial_net'] = df['commercial_long'] - df['commercial_short']
                
                # Keep only essential columns
                df = df[['cot_date', 'commercial_long', 'commercial_short', 'commercial_net']]
                dfs.append(df)
                
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue
        
        if dfs:
            self.cot_data = pd.concat(dfs, ignore_index=True)
            self.cot_data = self.cot_data.sort_values('cot_date')
            self.cot_data = self.cot_data.drop_duplicates('cot_date')
            print(f"✅ Loaded {len(self.cot_data)} COT reports")
            return True
        return False
    
    def load_price_data(self, pair="USDZAR=X", start_date="2020-01-01"):
        """Load USD/ZAR price data from Yahoo Finance"""
        try:
            # Download data
            self.price_data = yf.download(pair, start=start_date, interval="1d")
            self.price_data.columns = [col.lower() for col in self.price_data.columns]
            print(f"✅ Loaded {len(self.price_data)} days of price data")
            return True
        except Exception as e:
            print(f"Error loading price data: {e}")
            # Fallback: Create sample data for testing
            self._create_sample_price_data()
            return True
    
    def _create_sample_price_data(self):
        """Create sample price data if Yahoo Finance fails"""
        dates = pd.date_range(start="2020-01-01", end="2025-12-10", freq='D')
        np.random.seed(42)
        
        # Start around 17.0 and add random walk
        prices = [17.0]
        for i in range(1, len(dates)):
            change = np.random.normal(0, 0.002)  # 20 pip daily move avg
            prices.append(prices[-1] + change)
        
        self.price_data = pd.DataFrame({
            'open': prices,
            'high': [p + abs(np.random.normal(0, 0.001)) for p in prices],
            'low': [p - abs(np.random.normal(0, 0.001)) for p in prices],
            'close': prices,
            'adj close': prices,
            'volume': [1000000] * len(dates)
        }, index=dates)
        print("📝 Created sample price data for testing")
    
    def merge_data(self):
        """Merge COT data with price data for backtesting"""
        if self.cot_data is None or self.price_data is None:
            print("❌ No data loaded")
            return False
        
        results = []
        
        for _, cot_row in self.cot_data.iterrows():
            cot_date = cot_row['cot_date']
            commercial_net = cot_row['commercial_net']
            
            # Find price data for the week AFTER COT report
            # COT comes out Friday, we trade next week
            trade_start = cot_date + timedelta(days=3)  # Monday
            trade_end = trade_start + timedelta(days=5)  # Friday
            
            # Get price data for that week
            week_prices = self.price_data.loc[trade_start:trade_end]
            
            if len(week_prices) > 0:
                entry_price = week_prices.iloc[0]['open']  # Monday open
                exit_price = week_prices.iloc[-1]['close']  # Friday close
                week_high = week_prices['high'].max()
                week_low = week_prices['low'].min()
                
                # Calculate weekly return (in pips, 1 pip = 0.0001)
                pips_change = (exit_price - entry_price) * 10000
                
                results.append({
                    'cot_date': cot_date,
                    'commercial_net': commercial_net,
                    'entry_date': trade_start,
                    'entry_price': entry_price,
                    'exit_date': trade_end,
                    'exit_price': exit_price,
                    'week_high': week_high,
                    'week_low': week_low,
                    'pips_change': pips_change,
                    'percent_change': (exit_price / entry_price - 1) * 100
                })
        
        self.merged_data = pd.DataFrame(results)
        print(f"✅ Merged {len(self.merged_data)} weeks of trading data")
        
        # Calculate basic stats
        if len(self.merged_data) > 0:
            total_weeks = len(self.merged_data)
            positive_weeks = len(self.merged_data[self.merged_data['pips_change'] > 0])
            win_rate = (positive_weeks / total_weeks) * 100
            
            print(f"📊 Basic Stats: {total_weeks} weeks, {win_rate:.1f}% positive weeks")
            print(f"📊 Average weekly change: {self.merged_data['pips_change'].mean():.1f} pips")
        
        return True
    
    def get_backtest_data(self):
        """Get the merged data for backtesting"""
        return self.merged_data.copy()
    
    def save_merged_data(self, filename="merged_cot_price_data.csv"):
        """Save merged data to CSV for inspection"""
        if self.merged_data is not None:
            self.merged_data.to_csv(filename, index=False)
            print(f"💾 Saved merged data to {filename}")
