import pandas as pd
from datetime import datetime

class COTAnalyzer:
    def __init__(self, data_paths):
        """Initialize with COT CSV files"""
        self.df = self._load_and_merge_data(data_paths)
        
    def _load_and_merge_data(self, paths):
        """Load all CSV files"""
        dfs = []
        for path in paths:
            try:
                df = pd.read_csv(path)
                # Find date column
                date_col = None
                for col in df.columns:
                    if 'date' in col.lower():
                        date_col = col
                        break
                
                if date_col:
                    df['Report_Date'] = pd.to_datetime(df[date_col])
                    dfs.append(df)
            except:
                continue
        
        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            if 'Report_Date' in merged.columns:
                merged = merged.sort_values('Report_Date', ascending=False)
            return merged
        return pd.DataFrame()
    
    def get_latest_signal(self):
        """Get simple trading signal"""
        if self.df.empty:
            return self._get_sample_signal()
        
        try:
            latest = self.df.iloc[0]
            
            # Get positions
            long_col = None
            short_col = None
            for col in latest.index:
                if 'prod_merc' in col.lower() and 'long' in col.lower():
                    long_col = col
                elif 'prod_merc' in col.lower() and 'short' in col.lower():
                    short_col = col
            
            commercial_long = latest.get(long_col, 0) if long_col else 0
            commercial_short = latest.get(short_col, 0) if short_col else 0
            net_commercial = commercial_long - commercial_short
            
            # Simple signal logic
            if net_commercial < -30000:
                gold_signal = "BEARISH GOLD"
                usdzar_bias = "BULLISH USD/ZAR"
                strength = "STRONG" if net_commercial < -50000 else "MODERATE"
            elif net_commercial > 30000:
                gold_signal = "BULLISH GOLD"
                usdzar_bias = "BEARISH USD/ZAR"
                strength = "STRONG" if net_commercial > 50000 else "MODERATE"
            else:
                gold_signal = "NEUTRAL GOLD"
                usdzar_bias = "NEUTRAL USD/ZAR"
                strength = "WEAK"
            
            # Format date
            report_date = latest.get('Report_Date', datetime.now())
            if hasattr(report_date, 'strftime'):
                date_str = report_date.strftime("%b %d, %Y")
            else:
                date_str = str(report_date)
            
            return {
                'report_date': date_str,
                'commercial_long': int(commercial_long),
                'commercial_short': int(commercial_short),
                'net_commercial': int(net_commercial),
                'gold_signal': gold_signal,
                'usdzar_bias': usdzar_bias,
                'signal_strength': strength
            }
            
        except:
            return self._get_sample_signal()
    
    def _get_sample_signal(self):
        """Return sample signal if no data"""
        return {
            'report_date': 'Nov 04, 2025',
            'commercial_long': 9805,
            'commercial_short': 69256,
            'net_commercial': -59451,
            'gold_signal': 'BEARISH GOLD',
            'usdzar_bias': 'BULLISH USD/ZAR',
            'signal_strength': 'STRONG'
        }
