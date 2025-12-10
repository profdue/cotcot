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
                elif 'Report_Date' in df.columns:
                    df['Report_Date'] = pd.to_datetime(df['Report_Date'])
                else:
                    # Try to find date column
                    for col in df.columns:
                        if 'date' in col.lower() or 'Date' in col:
                            df['Report_Date'] = pd.to_datetime(df[col])
                            break
                
                dfs.append(df)
            except Exception as e:
                print(f"Error loading {path}: {e}")
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            # Sort by date, most recent first
            if 'Report_Date' in merged_df.columns:
                merged_df = merged_df.sort_values('Report_Date', ascending=False)
            return merged_df
        else:
            return pd.DataFrame()
    
    def get_latest_signal(self):
        """Extract the latest COT signal for Gold"""
        if self.df.empty or len(self.df) == 0:
            return {
                'error': 'No data loaded',
                'gold_signal': 'NEUTRAL',
                'usdzar_bias': 'NEUTRAL',
                'signal_strength': 'UNKNOWN'
            }
        
        latest = self.df.iloc[0]
        
        try:
            # Calculate commercial net position
            commercial_long = latest.get('Prod_Merc_Positions_Long_ALL', 0)
            commercial_short = latest.get('Prod_Merc_Positions_Short_ALL', 0)
            net_commercial = commercial_long - commercial_short
            
            # Calculate percentages
            open_interest = latest.get('Open_Interest_All', 1)
            commercial_long_pct = (commercial_long / open_interest) * 100 if open_interest > 0 else 0
            commercial_short_pct = (commercial_short / open_interest) * 100 if open_interest > 0 else 0
            
            # Determine signal
            signal = "NEUTRAL"
            usdzar_bias = "NEUTRAL"
            strength = "WEAK"
            
            if net_commercial < -50000:  # Commercials net short
                signal = "BEARISH GOLD"
                usdzar_bias = "BULLISH USD/ZAR"
                strength = "STRONG"
            elif net_commercial < -30000:
                signal = "BEARISH GOLD"
                usdzar_bias = "BULLISH USD/ZAR"
                strength = "MODERATE"
            elif net_commercial > 50000:  # Commercials net long
                signal = "BULLISH GOLD"
                usdzar_bias = "BEARISH USD/ZAR"
                strength = "STRONG"
            elif net_commercial > 30000:
                signal = "BULLISH GOLD"
                usdzar_bias = "BEARISH USD/ZAR"
                strength = "MODERATE"
            
            # Get report date
            report_date = latest.get('Report_Date')
            if hasattr(report_date, 'strftime'):
                report_date_str = report_date.strftime("%b %d, %Y")
            else:
                report_date_str = str(report_date)
            
            return {
                'report_date': report_date_str,
                'market': latest.get('Market_and_Exchange_Names', 'Unknown'),
                'open_interest': int(open_interest),
                'commercial_long': int(commercial_long),
                'commercial_short': int(commercial_short),
                'net_commercial': int(net_commercial),
                'commercial_long_pct': round(commercial_long_pct, 2),
                'commercial_short_pct': round(commercial_short_pct, 2),
                'gold_signal': signal,
                'usdzar_bias': usdzar_bias,
                'signal_strength': strength
            }
            
        except Exception as e:
            return {
                'error': f'Error processing data: {str(e)}',
                'gold_signal': 'NEUTRAL',
                'usdzar_bias': 'NEUTRAL',
                'signal_strength': 'UNKNOWN'
            }
    
    def get_historical_signals(self, limit=20):
        """Get last N signals for analysis"""
        if self.df.empty or len(self.df) == 0:
            return []
        
        try:
            signals = []
            for idx, row in self.df.head(limit).iterrows():
                commercial_long = row.get('Prod_Merc_Positions_Long_ALL', 0)
                commercial_short = row.get('Prod_Merc_Positions_Short_ALL', 0)
                net_commercial = commercial_long - commercial_short
                
                signal = "NEUTRAL"
                if net_commercial < -30000:
                    signal = "BEARISH"
                elif net_commercial > 30000:
                    signal = "BULLISH"
                
                # Get date
                report_date = row.get('Report_Date')
                if hasattr(report_date, 'strftime'):
                    date_str = report_date.strftime("%Y-%m-%d")
                else:
                    date_str = str(report_date)
                
                signals.append({
                    'date': date_str,
                    'net_commercial': int(net_commercial),
                    'signal': signal,
                    'open_interest': int(row.get('Open_Interest_All', 0))
                })
            
            return signals
            
        except Exception as e:
            print(f"Error getting historical signals: {e}")
            return []
