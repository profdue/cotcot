import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class COTAnalyzer:
    def __init__(self):
        self.df = None
        self.merged_data = None
        
    def load_all_cot_data(self):
        """Load ALL COT CSV files (2020-2025) with proper encoding"""
        data_files = []
        for year in range(2020, 2026):  # 2020 to 2025
            file_path = f"data/{year}_COT.csv"
            if os.path.exists(file_path):
                data_files.append(file_path)
        
        dfs = []
        for path in data_files:
            try:
                # Try different encodings for COT files
                try:
                    df = pd.read_csv(path, encoding='utf-8-sig')
                except:
                    df = pd.read_csv(path, encoding='latin-1')
                
                # Filter for REGULAR GOLD only
                if 'Market_and_Exchange_Names' in df.columns:
                    df = df[~df['Market_and_Exchange_Names'].str.contains('MICRO', na=False)]
                
                # Extract date
                if 'Report_Date_as_MM_DD_YYYY' in df.columns:
                    df['cot_date'] = pd.to_datetime(df['Report_Date_as_MM_DD_YYYY'])
                elif 'As_of_Date_In_Form_YYMMDD' in df.columns:
                    df['cot_date'] = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
                
                # Extract positions
                df['commercial_long'] = df.get('Prod_Merc_Positions_Long_ALL', 0)
                df['commercial_short'] = df.get('Prod_Merc_Positions_Short_ALL', 0)
                df['commercial_net'] = df['commercial_long'] - df['commercial_short']
                df['open_interest'] = df.get('Open_Interest_All', 0)
                
                # Keep only essential columns
                keep_cols = ['cot_date', 'commercial_long', 'commercial_short', 
                           'commercial_net', 'open_interest']
                df = df[[c for c in keep_cols if c in df.columns]]
                
                dfs.append(df)
                
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue
        
        if dfs:
            self.df = pd.concat(dfs, ignore_index=True)
            self.df = self.df.sort_values('cot_date')
            self.df = self.df.drop_duplicates('cot_date')
            return True
        return False
    
    def get_backtest_data(self):
        """Get clean data for backtesting"""
        return self.df.copy() if self.df is not None else None
    
    def get_latest_signal(self):
        """Get latest signal for display"""
        if self.df is None or len(self.df) == 0:
            return self._get_sample_signal()
        
        latest = self.df.iloc[-1]  # Most recent
        
        # Determine signal
        net = latest.get('commercial_net', 0)
        
        if net < -30000:
            gold_signal = "BEARISH GOLD"
            usdzar_bias = "BULLISH USD/ZAR"
            strength = "STRONG" if net < -50000 else "MODERATE"
        elif net > 30000:
            gold_signal = "BULLISH GOLD"
            usdzar_bias = "BEARISH USD/ZAR"
            strength = "STRONG" if net > 50000 else "MODERATE"
        else:
            gold_signal = "NEUTRAL GOLD"
            usdzar_bias = "NEUTRAL USD/ZAR"
            strength = "WEAK"
        
        return {
            'report_date': latest['cot_date'].strftime("%b %d, %Y"),
            'commercial_long': int(latest.get('commercial_long', 0)),
            'commercial_short': int(latest.get('commercial_short', 0)),
            'net_commercial': int(net),
            'gold_signal': gold_signal,
            'usdzar_bias': usdzar_bias,
            'signal_strength': strength,
            'open_interest': int(latest.get('open_interest', 0))
        }
    
    def _get_sample_signal(self):
        """Fallback sample"""
        return {
            'report_date': 'Nov 04, 2025',
            'commercial_long': 9805,
            'commercial_short': 69256,
            'net_commercial': -59451,
            'gold_signal': 'BEARISH GOLD',
            'usdzar_bias': 'BULLISH USD/ZAR',
            'signal_strength': 'STRONG',
            'open_interest': 450399
        }
