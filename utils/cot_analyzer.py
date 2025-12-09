import pandas as pd
from datetime import datetime

class COTAnalyzer:
    def __init__(self, data_paths):
        """
        Initialize with paths to COT CSV files
        """
        self.df = self._load_and_merge_data(data_paths)
        
    def _load_and_merge_data(self, paths):
        """Load and merge multiple COT CSV files"""
        dfs = []
        for path in paths:
            try:
                df = pd.read_csv(path)
                # Standardize date column
                if 'Report_Date_as_MM_DD_YYYY' in df.columns:
                    df['Report_Date'] = pd.to_datetime(df['Report_Date_as_MM_DD_YYYY'])
                dfs.append(df)
            except Exception as e:
                print(f"Error loading {path}: {e}")
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df = merged_df.sort_values('Report_Date', ascending=False)
            return merged_df
        else:
            return pd.DataFrame()
    
    def get_latest_signal(self):
        """Extract the latest COT signal for Gold"""
        if self.df.empty:
            return {"error": "No data loaded"}
        
        latest = self.df.iloc[0]
        
        # Calculate commercial net position
        commercial_long = latest.get('Prod_Merc_Positions_Long_ALL', 0)
        commercial_short = latest.get('Prod_Merc_Positions_Short_ALL', 0)
        net_commercial = commercial_long - commercial_short
        
        # Calculate percentages
        open_interest = latest.get('Open_Interest_All', 1)
        commercial_long_pct = (commercial_long / open_interest) * 100
        commercial_short_pct = (commercial_short / open_interest) * 100
        
        # Determine signal
        signal = "NEUTRAL"
        usdzar_bias = "NEUTRAL"
        
        if net_commercial < -50000:  # Commercials net short
            signal = "BEARISH GOLD"
            usdzar_bias = "BULLISH USD/ZAR"
            strength = "STRONG"
        elif net_commercial > 50000:  # Commercials net long
            signal = "BULLISH GOLD"
            usdzar_bias = "BEARISH USD/ZAR"
            strength = "STRONG"
        else:
            strength = "WEAK"
        
        return {
            'report_date': latest.get('Report_Date'),
            'market': latest.get('Market_and_Exchange_Names', 'Unknown'),
            'open_interest': open_interest,
            'commercial_long': commercial_long,
            'commercial_short': commercial_short,
            'net_commercial': net_commercial,
            'commercial_long_pct': round(commercial_long_pct, 2),
            'commercial_short_pct': round(commercial_short_pct, 2),
            'gold_signal': signal,
            'usdzar_bias': usdzar_bias,
            'signal_strength': strength,
            'raw_data': latest
        }
    
    def get_historical_signals(self, limit=20):
        """Get last N signals for analysis"""
        if self.df.empty:
            return []
        
        signals = []
        for idx, row in self.df.head(limit).iterrows():
            commercial_long = row.get('Prod_Merc_Positions_Long_ALL', 0)
            commercial_short = row.get('Prod_Merc_Positions_Short_ALL', 0)
            net_commercial = commercial_long - commercial_short
            
            signal = "NEUTRAL"
            if net_commercial < -50000:
                signal = "BEARISH"
            elif net_commercial > 50000:
                signal = "BULLISH"
            
            signals.append({
                'date': row.get('Report_Date'),
                'net_commercial': net_commercial,
                'signal': signal,
                'open_interest': row.get('Open_Interest_All', 0)
            })
        
        return signals
