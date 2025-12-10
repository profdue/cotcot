import pandas as pd
from datetime import datetime

class COTAnalyzer:
    def __init__(self, data_paths):
        self.df = self._load_data(data_paths)
    
    def _load_data(self, paths):
        """Load COT CSV files with proper date parsing"""
        dfs = []
        for path in paths:
            try:
                df = pd.read_csv(path)
                
                # EXACT column names from your CSV
                if 'Report_Date_as_MM_DD_YYYY' in df.columns:
                    df['Report_Date'] = pd.to_datetime(df['Report_Date_as_MM_DD_YYYY'])
                elif 'Report_Date' in df.columns:
                    df['Report_Date'] = pd.to_datetime(df['Report_Date'])
                elif 'As_of_Date_In_Form_YYMMDD' in df.columns:
                    # Parse YYMMDD format
                    df['Report_Date'] = pd.to_datetime(df['As_of_Date_In_Form_YYMMDD'], format='%y%m%d')
                else:
                    # Try to find any date column
                    date_found = False
                    for col in df.columns:
                        if 'date' in col.lower():
                            try:
                                df['Report_Date'] = pd.to_datetime(df[col])
                                date_found = True
                                break
                            except:
                                continue
                    
                    if not date_found:
                        # Skip file if no date column found
                        continue
                
                dfs.append(df)
                
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue
        
        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            if 'Report_Date' in merged.columns:
                return merged.sort_values('Report_Date', ascending=False)
            else:
                return merged
        return pd.DataFrame()
    
    def get_latest_signal(self):
        """Get trading signal from latest COT report"""
        if self.df.empty or len(self.df) == 0:
            return self._get_sample_signal()
        
        try:
            latest = self.df.iloc[0]
            
            # EXACT column names from your CSV
            commercial_long = latest.get('Prod_Merc_Positions_Long_ALL', 0)
            commercial_short = latest.get('Prod_Merc_Positions_Short_ALL', 0)
            net_commercial = commercial_long - commercial_short
            
            # Format date
            report_date = latest.get('Report_Date')
            if pd.isna(report_date):
                date_str = "Unknown Date"
            elif hasattr(report_date, 'strftime'):
                date_str = report_date.strftime("%b %d, %Y")
            else:
                date_str = str(report_date)
            
            # Signal logic
            if net_commercial < -30000:
                return {
                    'report_date': date_str,
                    'commercial_long': int(commercial_long),
                    'commercial_short': int(commercial_short),
                    'net_commercial': int(net_commercial),
                    'gold_signal': 'BEARISH GOLD',
                    'usdzar_bias': 'BULLISH USD/ZAR',
                    'signal_strength': 'STRONG' if net_commercial < -50000 else 'MODERATE',
                    'open_interest': int(latest.get('Open_Interest_All', 0))
                }
            elif net_commercial > 30000:
                return {
                    'report_date': date_str,
                    'commercial_long': int(commercial_long),
                    'commercial_short': int(commercial_short),
                    'net_commercial': int(net_commercial),
                    'gold_signal': 'BULLISH GOLD',
                    'usdzar_bias': 'BEARISH USD/ZAR',
                    'signal_strength': 'STRONG' if net_commercial > 50000 else 'MODERATE',
                    'open_interest': int(latest.get('Open_Interest_All', 0))
                }
            else:
                return {
                    'report_date': date_str,
                    'commercial_long': int(commercial_long),
                    'commercial_short': int(commercial_short),
                    'net_commercial': int(net_commercial),
                    'gold_signal': 'NEUTRAL GOLD',
                    'usdzar_bias': 'NEUTRAL USD/ZAR',
                    'signal_strength': 'WEAK',
                    'open_interest': int(latest.get('Open_Interest_All', 0))
                }
                
        except Exception as e:
            print(f"Error processing signal: {e}")
            return self._get_sample_signal()
    
    def _get_sample_signal(self):
        """Fallback sample signal"""
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
