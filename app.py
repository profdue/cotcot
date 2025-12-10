import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import modules
try:
    from cot_analyzer import COTAnalyzer
    from backtester import Backtester
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    # Minimal fallbacks
    class COTAnalyzer:
        def __init__(self): 
            self.df = None
        def load_all_cot_data(self): return False
        def get_backtest_data(self): return None
    
    class Backtester:
        def __init__(self, data, price_data=None):
            self.cot_data = data
            self.price_data = price_data

# Page config
st.set_page_config(
    page_title="COT Backtesting Lab - REAL USD/ZAR DATA",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 COT Backtesting Lab - REAL USD/ZAR DATA")
st.markdown("**Analyze 6 Years of COT Data with ACTUAL Price Performance**")

# Initialize session state
if 'cot_data' not in st.session_state:
    st.session_state.cot_data = None
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'backtest_report' not in st.session_state:
    st.session_state.backtest_report = None
if 'backtester' not in st.session_state:
    st.session_state.backtester = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Data Overview", "🔬 Strategy Analysis", "📈 Performance"])

# ============================================
# TAB 1: Data Overview
# ============================================
with tab1:
    st.header("📊 COT & USD/ZAR Data Overview (2020-2025)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📂 LOAD ALL COT DATA", type="primary", use_container_width=True):
            with st.spinner("Loading 6 years of COT data..."):
                analyzer = COTAnalyzer()
                if analyzer.load_all_cot_data():
                    st.session_state.cot_data = analyzer.get_backtest_data()
                    st.session_state.analyzer = analyzer
                    
                    if st.session_state.cot_data is not None:
                        df = st.session_state.cot_data
                        
                        st.success(f"""
                        ✅ **COT DATA LOADED!**
                        
                        **COT Summary:**
                        • {len(df)} weekly COT reports
                        • From {df['cot_date'].min().date()} to {df['cot_date'].max().date()}
                        • Commercial Net Range: {df['commercial_net'].min():,} to {df['commercial_net'].max():,}
                        • Average Commercial Net: {df['commercial_net'].mean():,.0f}
                        """)
                        
                        # Show data preview
                        with st.expander("📋 Preview COT Data"):
                            st.dataframe(df.head(10))
                        
                        # Commercial Net chart
                        fig = px.line(df, x='cot_date', y='commercial_net',
                                     title="Commercial Trader Positioning in Gold")
                        fig.add_hline(y=-50000, line_dash="dash", line_color="red",
                                     annotation_text="Strong Short Threshold")
                        fig.add_hline(y=-20000, line_dash="dot", line_color="orange",
                                     annotation_text="Moderate Short Threshold")
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        st.error("Failed to load COT data")
                else:
                    st.error("No COT files found in data/ folder")
    
    with col2:
        if st.button("💹 LOAD USD/ZAR PRICES", type="secondary", use_container_width=True):
            with st.spinner("Loading USD/ZAR historical data..."):
                try:
                    # Try different approaches to load the price data
                    backtester = Backtester(None)
                    
                    # Method 1: Use backtester's load method
                    if backtester.load_price_data("data/usd_zar_historical_data.csv"):
                        price_df = backtester.price_data
                        
                        st.session_state.price_data = price_df
                        
                        st.success(f"""
                        ✅ **USD/ZAR DATA LOADED!**
                        
                        **Price Summary:**
                        • {len(price_df)} trading days
                        • From {price_df['date'].min().date()} to {price_df['date'].max().date()}
                        • Price Range: {price_df['price'].min():.4f} to {price_df['price'].max():.4f}
                        • Current: {price_df['price'].iloc[-1]:.4f}
                        """)
                        
                        # Show preview of data
                        with st.expander("📋 Preview Price Data"):
                            st.dataframe(price_df.head(10))
                        
                        # Show price chart
                        fig = px.line(price_df, x='date', y='price',
                                     title="USD/ZAR Historical Price")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Price distribution
                        fig2 = px.histogram(price_df, x='price', nbins=30,
                                          title="USD/ZAR Price Distribution")
                        st.plotly_chart(fig2, use_container_width=True)
                        
                    else:
                        # Method 2: Manual loading as fallback
                        st.warning("Using fallback loading method...")
                        
                        # Read file manually
                        import csv
                        dates = []
                        prices = []
                        
                        with open("data/usd_zar_historical_data.csv", 'r', encoding='utf-8-sig') as f:
                            reader = csv.reader(f)
                            # Try to read header
                            try:
                                header = next(reader)
                            except:
                                header = []
                            
                            for row in reader:
                                if len(row) >= 2:
                                    try:
                                        date_str = row[0].strip().strip('"')
                                        price_str = row[1].strip().strip('"').replace(',', '')
                                        
                                        date = pd.to_datetime(date_str, dayfirst=True)
                                        price = float(price_str)
                                        
                                        dates.append(date)
                                        prices.append(price)
                                    except:
                                        continue
                        
                        if dates:
                            price_df = pd.DataFrame({'date': dates, 'price': prices})
                            price_df = price_df.dropna()
                            price_df = price_df.sort_values('date')
                            st.session_state.price_data = price_df
                            
                            st.success(f"✅ Loaded {len(price_df)} price records manually")
                        else:
                            st.error("Could not load price data with any method")
                            
                except Exception as e:
                    st.error(f"Error loading price data: {str(e)}")
                    st.info("""
                    **Troubleshooting:**
                    1. Check file exists at `data/usd_zar_historical_data.csv`
                    2. Ensure file is comma-separated with quotes
                    3. Format: `"Date","Price","Open","High","Low","Vol.","Change %"`
                    """)
    
    # Show combined data if both loaded
    if st.session_state.cot_data is not None and st.session_state.price_data is not None:
        st.subheader("📈 Combined Data Analysis")
        
        # Create backtester instance
        backtester = Backtester(st.session_state.cot_data, st.session_state.price_data)
        st.session_state.backtester = backtester
        
        # Commercial Net vs Price overlay
        fig = go.Figure()
        
        # Add price (right axis)
        price_df = st.session_state.price_data
        fig.add_trace(go.Scatter(
            x=price_df['date'],
            y=price_df['price'],
            name="USD/ZAR Price",
            line=dict(color='blue', width=2),
            yaxis="y2"
        ))
        
        # Add commercial net (left axis)
        cot_df = st.session_state.cot_data
        fig.add_trace(go.Scatter(
            x=cot_df['cot_date'],
            y=cot_df['commercial_net'],
            name="Commercial Net (Gold)",
            line=dict(color='red', width=1),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.1)'
        ))
        
        fig.update_layout(
            title="Commercial Gold Positioning vs USD/ZAR Price",
            yaxis=dict(
                title="Commercial Net Position (Gold)",
                side="left",
                showgrid=False
            ),
            yaxis2=dict(
                title="USD/ZAR Price",
                side="right",
                overlaying="y",
                showgrid=True
            ),
            hovermode='x unified',
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Correlation analysis
        st.subheader("📊 Correlation Analysis")
        
        # Align dates for correlation
        aligned = backtester.align_cot_with_prices()
        if aligned is not None and len(aligned) > 0:
            correlation = aligned[['commercial_net', 'price_change']].corr().iloc[0, 1]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Correlation Coefficient", f"{correlation:.3f}")
            with col2:
                st.metric("Aligned Data Points", len(aligned))
            with col3:
                avg_holding = aligned['holding_days'].mean()
                st.metric("Avg Holding Days", f"{avg_holding:.1f}")
            
            # Scatter plot
            fig = px.scatter(aligned, x='commercial_net', y='price_change',
                           title="Commercial Net vs USD/ZAR Price Change",
                           trendline="ols",
                           labels={'commercial_net': 'Commercial Net Position', 
                                  'price_change': 'USD/ZAR Price Change'})
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 2: Strategy Analysis
# ============================================
with tab2:
    st.header("🔬 Strategy Analysis with REAL Prices")
    
    if st.session_state.cot_data is None:
        st.warning("⚠️ Please load COT data in Tab 1 first!")
    elif st.session_state.price_data is None:
        st.warning("⚠️ Please load USD/ZAR price data in Tab 1 first!")
    else:
        # Ensure backtester is initialized
        if st.session_state.backtester is None:
            st.session_state.backtester = Backtester(
                st.session_state.cot_data, 
                st.session_state.price_data
            )
        
        backtester = st.session_state.backtester
        
        # Disclaimer
        st.info("""
        **Strategy:** Buy USD/ZAR when Commercial Gold Net Position < Threshold  
        **Hold Time:** 1 week (approx. 5-7 trading days)  
        **Costs:** 3-pip spread included  
        **Risk:** 1% per trade, 50-pip stop loss assumed
        """)
        
        st.subheader("🧪 Test Different Thresholds")
        
        if st.button("🚀 RUN COMPREHENSIVE BACKTEST", type="primary"):
            with st.spinner("Running backtest with actual prices..."):
                threshold_df = backtester.analyze_thresholds()
                
                if len(threshold_df) > 0:
                    # Find best by profit factor (with minimum trades filter)
                    valid_df = threshold_df[threshold_df['trades'] >= 10]
                    
                    if len(valid_df) > 0:
                        best_idx = valid_df['profit_factor'].idxmax()
                        best_row = valid_df.loc[best_idx]
                        
                        st.success(f"""
                        🏆 **OPTIMAL STRATEGY FOUND!**
                        
                        **Threshold:** Commercial Net < {best_row['threshold']:,}  
                        **Trades:** {best_row['trades']}  
                        **Win Rate:** {best_row['win_rate']}%  
                        **Profit Factor:** {best_row['profit_factor']}  
                        **Total Pips:** {best_row['total_pips']}  
                        **Max Drawdown:** {best_row['max_drawdown_pct']}%
                        """)
                        
                        # Show detailed table
                        st.subheader("📊 Threshold Performance Comparison")
                        display_df = threshold_df.sort_values('profit_factor', ascending=False)
                        st.dataframe(
                            display_df.style.format({
                                'threshold': '{:,}',
                                'win_rate': '{:.1f}%',
                                'avg_pips': '{:.1f}',
                                'total_pips': '{:.1f}',
                                'profit_factor': '{:.2f}',
                                'max_drawdown_pct': '{:.1f}%'
                            }),
                            use_container_width=True
                        )
                        
                        # Store best threshold
                        st.session_state.best_threshold = best_row['threshold']
                        
                        # Show equity curve for best threshold
                        trades_df = backtester.backtest_threshold(best_row['threshold'])
                        if trades_df is not None:
                            fig = px.line(trades_df, x='entry_date', y='equity',
                                         title=f"Equity Curve (Threshold: {best_row['threshold']:,})",
                                         labels={'equity': 'Account Equity ($)', 'entry_date': 'Trade Date'})
                            fig.add_hline(y=10000, line_dash="dash", line_color="gray")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        st.warning("Not enough trades for reliable analysis. Try different thresholds.")
                else:
                    st.error("Backtest failed. Check data alignment.")
        
        # Detailed analysis for selected threshold
        st.subheader("📈 Analyze Specific Threshold")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            threshold = st.slider(
                "Select Commercial Net Threshold",
                min_value=-80000,
                max_value=0,
                value=-50000,
                step=5000,
                help="Buy USD/ZAR when Commercial Gold Net is below this value"
            )
        
        with col2:
            risk = st.selectbox(
                "Risk per Trade",
                options=[0.005, 0.01, 0.02, 0.03],
                index=1,
                format_func=lambda x: f"{x*100}%",
                help="Percentage of capital to risk per trade"
            )
        
        if st.button("📊 ANALYZE SELECTED THRESHOLD", type="secondary"):
            stats = backtester.get_strategy_stats(threshold)
            
            if stats:
                # Key metrics in columns
                st.subheader("📋 Strategy Performance Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", stats['total_trades'])
                    st.metric("Win Rate", f"{stats['win_rate']}%")
                
                with col2:
                    st.metric("Profit Factor", f"{stats['profit_factor']}")
                    st.metric("Sharpe Ratio", f"{stats['sharpe_ratio']}")
                
                with col3:
                    st.metric("Total Pips", f"{stats['total_pips']}")
                    st.metric("Max Drawdown", f"{stats['max_drawdown_pct']}%")
                
                with col4:
                    st.metric("Final Equity", f"${stats['final_equity']:,.0f}")
                    st.metric("ROI", f"{stats['roi_pct']}%")
                
                # Detailed metrics
                with st.expander("📈 Detailed Performance Metrics"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Win/Loss Analysis:**")
                        st.write(f"• Winning Trades: {stats['winning_trades']}")
                        st.write(f"• Losing Trades: {stats['losing_trades']}")
                        st.write(f"• Average Win: {stats['avg_win_pips']} pips")
                        st.write(f"• Average Loss: {stats['avg_loss_pips']} pips")
                        st.write(f"• Max Win: {stats['max_win_pips']} pips")
                        st.write(f"• Max Loss: {stats['max_loss_pips']} pips")
                    
                    with col2:
                        st.write("**Return Analysis:**")
                        st.write(f"• Total Profit: ${stats['total_profit']:,.0f}")
                        st.write(f"• Average Return: {stats['avg_return_pct']}%")
                        st.write(f"• Starting Capital: $10,000")
                        st.write(f"• Ending Capital: ${stats['final_equity']:,.2f}")
                        st.write(f"• Net Profit: ${stats['final_equity'] - 10000:,.2f}")
                
                # Monthly performance
                if 'monthly' in stats and stats['monthly']:
                    st.subheader("📅 Monthly Performance")
                    monthly_df = pd.DataFrame(stats['monthly'])
                    monthly_df['year_month'] = monthly_df['year_month'].astype(str)
                    
                    fig = px.bar(monthly_df, x='year_month', y='trade_profit',
                                title="Monthly Profit/Loss")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    with st.expander("View Monthly Data Table"):
                        st.dataframe(monthly_df)
            else:
                st.warning(f"No trades generated with threshold {threshold}. Try a different value.")

# ============================================
# TAB 3: Performance
# ============================================
with tab3:
    st.header("📈 Performance Metrics & Comparison")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("⚠️ Please load both datasets in Tab 1 first!")
    else:
        if st.session_state.backtester is None:
            st.session_state.backtester = Backtester(
                st.session_state.cot_data, 
                st.session_state.price_data
            )
        
        backtester = st.session_state.backtester
        
        st.subheader("🔄 Strategy Comparison")
        
        # Test multiple strategies
        thresholds = [-60000, -50000, -40000, -30000, -20000, -10000]
        
        comparison = []
        for thresh in thresholds:
            stats = backtester.get_strategy_stats(thresh)
            
            if stats:
                comparison.append({
                    'Threshold': thresh,
                    'Trades': stats['total_trades'],
                    'Win Rate %': stats['win_rate'],
                    'Profit Factor': stats['profit_factor'],
                    'Total Pips': stats['total_pips'],
                    'Max DD %': stats['max_drawdown_pct'],
                    'Sharpe': stats['sharpe_ratio'],
                    'Final Equity': f"${stats['final_equity']:,.0f}",
                    'ROI %': stats['roi_pct']
                })
        
        if comparison:
            comp_df = pd.DataFrame(comparison)
            
            # Sort by Profit Factor
            comp_df = comp_df.sort_values('Profit Factor', ascending=False)
            
            st.dataframe(
                comp_df.style.format({
                    'Win Rate %': '{:.1f}',
                    'Profit Factor': '{:.2f}',
                    'Total Pips': '{:.1f}',
                    'Max DD %': '{:.1f}',
                    'Sharpe': '{:.2f}',
                    'ROI %': '{:.1f}'
                }),
                use_container_width=True
            )
            
            # Visual comparisons
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.bar(comp_df, x='Threshold', y='Profit Factor',
                             title='Profit Factor by Threshold',
                             color='Profit Factor',
                             color_continuous_scale='RdYlGn')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.bar(comp_df, x='Threshold', y='Win Rate %',
                             title='Win Rate by Threshold',
                             color='Win Rate %',
                             color_continuous_scale='RdYlGn')
                st.plotly_chart(fig2, use_container_width=True)
        
        # Generate full report
        st.subheader("📄 Comprehensive Backtest Report")
        
        if st.button("📊 GENERATE FULL REPORT", type="primary"):
            with st.spinner("Generating detailed report..."):
                report = backtester.generate_report()
                st.session_state.backtest_report = report
                
                if 'error' not in report:
                    st.success("✅ Real Data Report Generated!")
                    
                    # Show key findings
                    st.subheader("🔑 Key Findings from 6 Years of Data")
                    
                    if 'best_threshold' in report:
                        best = report['best_threshold']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info(f"""
                            **Optimal Strategy Parameters:**
                            • **Entry Signal:** Commercial Net < {best['threshold']:,}
                            • **Expected Trades:** {best['trades']}
                            • **Win Rate:** {best['win_rate']}%
                            • **Profit Factor:** {best['profit_factor']}
                            """)
                        
                        with col2:
                            st.info(f"""
                            **Risk/Reward Profile:**
                            • **Avg Trade:** {best['avg_pips']} pips
                            • **Total Profit:** {best['total_pips']} pips
                            • **Max Drawdown:** {best['max_drawdown_pct']}%
                            • **Return/Risk Ratio:** {best['profit_factor']}
                            """)
                    
                    # Data statistics
                    if 'data_overview' in report:
                        data = report['data_overview']
                        
                        st.subheader("📊 Data Statistics")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**COT Data:**")
                            st.write(f"• Reports: {data['total_cot_weeks']}")
                            st.write(f"• Date Range: {data['cot_date_range']}")
                            st.write(f"• Avg Commercial Net: {data['avg_commercial_net']:,.0f}")
                        
                        with col2:
                            st.write("**USD/ZAR Data:**")
                            st.write(f"• Trading Days: {data['total_price_days']}")
                            st.write(f"• Date Range: {data['price_date_range']}")
                            st.write(f"• Price Range: {data['usdzar_range']}")
                        
                        with col3:
                            st.write("**Alignment:**")
                            if 'alignment_info' in report:
                                align = report['alignment_info']
                                st.write(f"• Aligned Trades: {align['aligned_trades']}")
                                st.write(f"• Alignment Rate: {align['successful_alignment_pct']}%")
                                st.write(f"• Avg Hold Days: {align['avg_holding_days']}")
                    
                    # Signal distribution
                    if 'signal_distribution' in report:
                        st.subheader("📈 Signal Frequency Distribution")
                        
                        signal_data = []
                        total_weeks = report['data_overview']['total_cot_weeks']
                        
                        for signal, count in report['signal_distribution'].items():
                            if pd.notna(signal):
                                percentage = (count / total_weeks) * 100
                                signal_data.append({
                                    'Signal': signal,
                                    'Weeks': count,
                                    'Percentage': percentage
                                })
                        
                        if signal_data:
                            signal_df = pd.DataFrame(signal_data)
                            signal_df = signal_df.sort_values('Weeks', ascending=False)
                            
                            fig = px.bar(signal_df, x='Signal', y='Percentage',
                                        title='How Often Each Signal Occurs',
                                        text='Weeks')
                            fig.update_traces(texttemplate='%{text} weeks', textposition='outside')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            with st.expander("View Signal Distribution Table"):
                                st.dataframe(signal_df)
                else:
                    st.error(f"Report generation failed: {report['error']}")

# Footer
st.divider()
st.caption("""
**COT Backtesting Lab v2.1 - REAL DATA EDITION** | 
COT Data: 2020-2025 | USD/ZAR Prices: 2020-2025 |
Strategy: Buy USD/ZAR when Commercial Gold Net < Threshold |
**Note:** Includes 3-pip spread cost. Past performance ≠ future results.
""")
