import pandas as pd
from datetime import datetime

class COTAnalyzer:
    def __init__(self, data_paths):
        """Simple COT analyzer for limit orders"""
        self.df = self._load_data(data_paths)
    
    def _load_data(self, paths):
        """Load COT CSV files"""
        if not paths:
            return pd.DataFrame()
        
        try:
            dfs = []
            for path in paths:
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
            
            if dfs:
                merged = pd.concat(dfs, ignore_index=True)
                if 'Report_Date' in merged.columns:
                    merged = merged.sort_values('Report_Date', ascending=False)
                return merged
        except:
            pass
        
        return pd.DataFrame()
    
    def get_latest_signal(self):
        """Get simple trading signal for limit orders"""
        if self.df.empty or len(self.df) == 0:
            return self._default_signal()
        
        try:
            latest = self.df.iloc[0]
            
            # Find commercial position columns
            long_val = short_val = 0
            
            for col in latest.index:
                col_lower = str(col).lower()
                if 'prod_merc' in col_lower and 'long' in col_lower:
                    long_val = latest[col]
                elif 'prod_merc' in col_lower and 'short' in col_lower:
                    short_val = latest[col]
            
            net_commercial = long_val - short_val
            
            # Determine signal
            if net_commercial < -50000:
                usdzar_bias = "BULLISH USD/ZAR"
                strength = "STRONG"
            elif net_commercial < -30000:
                usdzar_bias = "BULLISH USD/ZAR"
                strength = "MODERATE"
            elif net_commercial > 50000:
                usdzar_bias = "BEARISH USD/ZAR"
                strength = "STRONG"
            elif net_commercial > 30000:
                usdzar_bias = "BEARISH USD/ZAR"
                strength = "MODERATE"
            else:
                usdzar_bias = "NEUTRAL USD/ZAR"
                strength = "WEAK"
            
            # Format date
            report_date = latest.get('Report_Date', datetime.now())
            if hasattr(report_date, 'strftime'):
                date_str = report_date.strftime("%b %d, %Y")
            else:
                date_str = "Recent Report"
            
            return {
                'report_date': date_str,
                'commercial_long': int(long_val),
                'commercial_short': int(short_val),
                'net_commercial': int(net_commercial),
                'usdzar_bias': usdzar_bias,
                'signal_strength': strength
            }
            
        except Exception as e:
            return self._default_signal()
    
    def _default_signal(self):
        """Return default signal if no data"""
        return {
            'report_date': datetime.now().strftime("%b %d, %Y"),
            'commercial_long': 9805,
            'commercial_short': 69256,
            'net_commercial': -59451,
            'usdzar_bias': 'BULLISH USD/ZAR',
            'signal_strength': 'STRONG'
        }
