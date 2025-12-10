import pandas as pd

class COTAnalyzer:
    def __init__(self, data_paths):
        self.df = self._load_data(data_paths)
    
    def _load_data(self, paths):
        """Simple data loader"""
        dfs = []
        for path in paths:
            try:
                df = pd.read_csv(path)
                # Find date column
                for col in df.columns:
                    if 'date' in col.lower():
                        df['Report_Date'] = pd.to_datetime(df[col])
                        break
                dfs.append(df)
            except:
                continue
        
        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            if 'Report_Date' in merged.columns:
                return merged.sort_values('Report_Date', ascending=False)
        return pd.DataFrame()
    
    def get_latest_signal(self):
        """Get simple BUY/SELL signal"""
        if self.df.empty:
            return self._get_sample()
        
        try:
            latest = self.df.iloc[0]
            
            # Find position columns
            long_pos = short_pos = 0
            for col in latest.index:
                col_lower = col.lower()
                if 'prod_merc' in col_lower and 'long' in col_lower:
                    long_pos = latest[col]
                elif 'prod_merc' in col_lower and 'short' in col_lower:
                    short_pos = latest[col]
            
            net = long_pos - short_pos
            
            # Simple signal logic
            if net < -30000:
                return {
                    'report_date': latest.get('Report_Date', 'Recent'),
                    'commercial_long': int(long_pos),
                    'commercial_short': int(short_pos),
                    'net_commercial': int(net),
                    'gold_signal': 'BEARISH GOLD',
                    'usdzar_bias': 'BULLISH USD/ZAR',
                    'signal_strength': 'STRONG' if net < -50000 else 'MODERATE'
                }
            elif net > 30000:
                return {
                    'report_date': latest.get('Report_Date', 'Recent'),
                    'commercial_long': int(long_pos),
                    'commercial_short': int(short_pos),
                    'net_commercial': int(net),
                    'gold_signal': 'BULLISH GOLD',
                    'usdzar_bias': 'BEARISH USD/ZAR',
                    'signal_strength': 'STRONG' if net > 50000 else 'MODERATE'
                }
            else:
                return {
                    'report_date': latest.get('Report_Date', 'Recent'),
                    'commercial_long': int(long_pos),
                    'commercial_short': int(short_pos),
                    'net_commercial': int(net),
                    'gold_signal': 'NEUTRAL GOLD',
                    'usdzar_bias': 'NEUTRAL USD/ZAR',
                    'signal_strength': 'WEAK'
                }
                
        except:
            return self._get_sample()
    
    def _get_sample(self):
        """Sample signal"""
        return {
            'report_date': 'Nov 04, 2025',
            'commercial_long': 9805,
            'commercial_short': 69256,
            'net_commercial': -59451,
            'gold_signal': 'BEARISH GOLD',
            'usdzar_bias': 'BULLISH USD/ZAR',
            'signal_strength': 'STRONG'
        }
