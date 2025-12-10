import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sys
import os
from datetime import datetime

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
        def __init__(self, data=None, price_data=None):
            self.cot_data = data.copy() if data is not None else None
            self.price_data = price_data.copy() if price_data is not None else None
        def load_price_data(self, filepath): return False
        def get_strategy_stats(self, threshold): return None

# Custom price loader for DD/MM/YYYY dates
def load_price_data_custom(filepath="data/usd_zar_historical_data.csv"):
    """Custom loader that definitely handles DD/MM/YYYY dates"""
    try:
        # Read the CSV
        df = pd.read_csv(
            filepath,
            encoding='utf-8-sig',
            quotechar='"',
            thousands=',',
            engine='python'
        )
        
        # Clean column names
        df.columns = [col.strip().replace('"', '') for col in df.columns]
        
        # Find date and price columns
        date_col = 'Date' if 'Date' in df.columns else df.columns[0]
        price_col = 'Price' if 'Price' in df.columns else df.columns[1]
        
        # Parse DD/MM/YYYY dates
        def parse_dmy(date_str):
            try:
                # Remove quotes and whitespace
                date_str = str(date_str).strip().strip('"')
                # Split by /
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    # Handle 2-digit year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    return f"{year}-{month}-{day}"
            except:
                pass
            return None
        
        # Apply parser
        df['date_str'] = df[date_col].apply(parse_dmy)
        df['date'] = pd.to_datetime(df['date_str'], errors='coerce')
        
        # If that fails, try dayfirst=True
        if df['date'].isna().any():
            df['date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        
        # Convert price
        df['price'] = pd.to_numeric(
            df[price_col].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
        
        # Remove invalid rows
        df = df.dropna(subset=['date', 'price'])
        df = df.sort_values('date')
        
        return df[['date', 'price']]
        
    except Exception as e:
        st.error(f"Error loading price data: {e}")
        return None

# Page config
st.set_page_config(
    page_title="COT Backtesting Lab",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 COT Backtesting Lab - REAL 6-YEAR DATA")
st.markdown("**Analyze 6 Years of COT Data with 6 Years of USD/ZAR Prices**")

# Initialize session state
if 'cot_data' not in st.session_state:
    st.session_state.cot_data = None
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'backtester' not in st.session_state:
    st.session_state.backtester = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Data Loading", "🔬 Strategy Testing", "📈 Results"])

# ============================================
# TAB 1: Data Loading
# ============================================
with tab1:
    st.header("📊 Load Your Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. COT Data (2020-2025)")
        if st.button("📂 Load COT Data", type="primary", use_container_width=True):
            with st.spinner("Loading 6 years of COT data..."):
                analyzer = COTAnalyzer()
                if analyzer.load_all_cot_data():
                    st.session_state.cot_data = analyzer.get_backtest_data()
                    
                    if st.session_state.cot_data is not None:
                        df = st.session_state.cot_data
                        st.success(f"""
                        ✅ **COT Data Loaded Successfully!**
                        
                        **Summary:**
                        • {len(df)} weekly COT reports
                        • Date Range: {df['cot_date'].min().date()} to {df['cot_date'].max().date()}
                        • Commercial Net Range: {df['commercial_net'].min():,} to {df['commercial_net'].max():,}
                        • Average Commercial Net: {df['commercial_net'].mean():,.0f}
                        """)
                        
                        with st.expander("📋 View COT Data Sample"):
                            st.dataframe(df.head(10))
                        
                        # Commercial Net chart
                        fig = px.line(df, x='cot_date', y='commercial_net',
                                     title="Commercial Gold Positioning (2020-2025)",
                                     labels={'commercial_net': 'Commercial Net Position', 'cot_date': 'Date'})
                        fig.add_hline(y=0, line_dash="dash", line_color="gray")
                        fig.add_hline(y=-50000, line_dash="dot", line_color="red", 
                                     annotation_text="Strong Short Level")
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        st.error("Failed to load COT data")
                else:
                    st.error("No COT files found in data/ folder")
    
    with col2:
        st.subheader("2. USD/ZAR Price Data (2020-2025)")
        if st.button("💹 Load USD/ZAR Prices", type="secondary", use_container_width=True):
            with st.spinner("Loading 6 years of USD/ZAR prices..."):
                # Use custom loader
                price_df = load_price_data_custom()
                
                if price_df is not None and len(price_df) > 0:
                    st.session_state.price_data = price_df
                    
                    st.success(f"""
                    ✅ **USD/ZAR Prices Loaded Successfully!**
                    
                    **Summary:**
                    • {len(price_df)} trading days
                    • Date Range: {price_df['date'].min().date()} to {price_df['date'].max().date()}
                    • Price Range: {price_df['price'].min():.4f} to {price_df['price'].max():.4f}
                    • Current Price: {price_df['price'].iloc[-1]:.4f}
                    """)
                    
                    with st.expander("📋 View Price Data Sample"):
                        st.dataframe(price_df.head(10))
                    
                    # Price chart
                    fig = px.line(price_df, x='date', y='price',
                                 title="USD/ZAR Historical Price (2020-2025)",
                                 labels={'price': 'USD/ZAR Rate', 'date': 'Date'})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Price distribution
                    fig2 = px.histogram(price_df, x='price', nbins=30,
                                      title="USD/ZAR Price Distribution")
                    st.plotly_chart(fig2, use_container_width=True)
                    
                else:
                    st.error("Could not load price data or file is empty")
    
    # Show data status and initialize backtester
    st.subheader("📋 Data Status")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        if st.session_state.cot_data is not None:
            df = st.session_state.cot_data
            st.success(f"✅ COT Data: {len(df)} weeks")
            st.caption(f"{df['cot_date'].min().date()} to {df['cot_date'].max().date()}")
        else:
            st.warning("⚠️ COT Data: Not Loaded")
    
    with status_col2:
        if st.session_state.price_data is not None:
            df = st.session_state.price_data
            st.success(f"✅ USD/ZAR Prices: {len(df)} days")
            st.caption(f"{df['date'].min().date()} to {df['date'].max().date()}")
        else:
            st.warning("⚠️ USD/ZAR Prices: Not Loaded")
    
    with status_col3:
        if st.session_state.cot_data is not None and st.session_state.price_data is not None:
            # Initialize backtester
            st.session_state.backtester = Backtester(
                st.session_state.cot_data,
                st.session_state.price_data
            )
            st.success("✅ Backtester Ready!")
            st.caption("Go to Strategy Testing tab")
        else:
            st.info("⏳ Load both datasets to begin")
    
    # Show combined view when both loaded
    if st.session_state.cot_data is not None and st.session_state.price_data is not None:
        st.subheader("📈 Combined Data View")
        
        # Create combined chart
        fig = go.Figure()
        
        # Add price on right axis
        price_df = st.session_state.price_data
        fig.add_trace(go.Scatter(
            x=price_df['date'],
            y=price_df['price'],
            name="USD/ZAR Price",
            line=dict(color='blue', width=2),
            yaxis="y2"
        ))
        
        # Add commercial net on left axis
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
            title="Commercial Gold Positioning vs USD/ZAR Price (2020-2025)",
            yaxis=dict(
                title="Commercial Net Position",
                side="left",
                titlefont=dict(color="red"),
                tickfont=dict(color="red")
            ),
            yaxis2=dict(
                title="USD/ZAR Price",
                side="right",
                overlaying="y",
                titlefont=dict(color="blue"),
                tickfont=dict(color="blue")
            ),
            hovermode='x unified',
            legend=dict(x=0.02, y=0.98),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Data alignment check
        st.subheader("🔍 Data Alignment Check")
        
        if st.button("🔗 Check Data Alignment", type="secondary"):
            backtester = Backtester(st.session_state.cot_data, st.session_state.price_data)
            aligned_df = backtester.align_cot_with_prices()
            
            if aligned_df is not None and len(aligned_df) > 0:
                st.success(f"✅ Data Alignment Successful!")
                st.write(f"**Aligned {len(aligned_df)} trades for backtesting**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Holding Days", f"{aligned_df['holding_days'].mean():.1f}")
                with col2:
                    st.metric("Date Range", f"{aligned_df['cot_date'].min().date()} to {aligned_df['cot_date'].max().date()}")
                with col3:
                    avg_return = aligned_df['pct_return'].mean()
                    st.metric("Average Return", f"{avg_return:.2f}%")
                
                with st.expander("📋 View Aligned Trades Sample"):
                    st.dataframe(aligned_df[['cot_date', 'entry_date', 'entry_price', 'exit_price', 'pips']].head(10))
            else:
                st.error("❌ Data Alignment Failed")
                st.info("""
                **Possible Issues:**
                1. Date formats don't match
                2. Date ranges don't overlap
                3. Missing price data for COT dates
                
                **Check:**
                - COT dates: Tuesdays (weekly)
                - Price dates: Daily trading days
                - Ensure date ranges overlap (2020-2025)
                """)

# ============================================
# TAB 2: Strategy Testing
# ============================================
with tab2:
    st.header("🔬 Strategy Testing")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("⚠️ Please load both datasets in the Data Loading tab first!")
        st.info("""
        **Required:**
        1. COT Data (2020-2025 weekly reports)
        2. USD/ZAR Prices (2020-2025 daily prices)
        
        **Then click "Check Data Alignment" in Tab 1** to verify dates match.
        """)
    else:
        # Initialize backtester if not done
        if st.session_state.backtester is None:
            st.session_state.backtester = Backtester(
                st.session_state.cot_data,
                st.session_state.price_data
            )
        
        backtester = st.session_state.backtester
        
        st.info("""
        **💰 Strategy Logic:**
        - **Signal:** Commercial Gold Net Position < Threshold
        - **Action:** Buy USD/ZAR (go long)
        - **Entry:** Next trading day after COT report
        - **Exit:** 1 week later (approx. 5-7 trading days)
        - **Costs:** 3-pip spread included
        - **Risk:** 1% per trade, 50-pip stop loss
        """)
        
        # Single threshold test
        st.subheader("🧪 Test Single Threshold")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            threshold = st.slider(
                "Commercial Net Threshold",
                min_value=-150000,
                max_value=0,
                value=-50000,
                step=10000,
                help="Buy USD/ZAR when Commercial Gold Net is below this value"
            )
        
        with col2:
            st.metric("Current Threshold", f"{threshold:,}")
        
        if st.button("🚀 Run Backtest for This Threshold", type="primary", use_container_width=True):
            with st.spinner(f"Running backtest with threshold {threshold:,}..."):
                stats = backtester.get_strategy_stats(threshold)
                
                if stats:
                    st.success(f"✅ Backtest Complete!")
                    
                    # Display key results
                    st.subheader("📊 Performance Summary")
                    
                    # Top metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Trades", stats['total_trades'])
                        st.metric("Win Rate", f"{stats['win_rate']}%")
                    
                    with col2:
                        st.metric("Profit Factor", f"{stats['profit_factor']:.2f}")
                        st.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
                    
                    with col3:
                        st.metric("Total Pips", f"{stats['total_pips']:,.1f}")
                        st.metric("Max Drawdown", f"{stats['max_drawdown_pct']}%")
                    
                    with col4:
                        st.metric("Final Equity", f"${stats['final_equity']:,.0f}")
                        st.metric("ROI", f"{stats['roi_pct']}%")
                    
                    # Detailed metrics
                    with st.expander("📈 Detailed Performance Analysis"):
                        st.write("**Trade Statistics:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"- **Winning Trades:** {stats['winning_trades']}")
                            st.write(f"- **Losing Trades:** {stats['losing_trades']}")
                            st.write(f"- **Avg Win:** {stats['avg_win_pips']} pips")
                            st.write(f"- **Avg Loss:** {stats['avg_loss_pips']} pips")
                            st.write(f"- **Max Win:** {stats['max_win_pips']} pips")
                        
                        with col2:
                            st.write(f"- **Max Loss:** {stats['max_loss_pips']} pips")
                            st.write(f"- **Avg Return:** {stats['avg_return_pct']}%")
                            st.write(f"- **Total Profit:** ${stats['total_profit']:,.0f}")
                            st.write(f"- **Starting Capital:** $10,000")
                            st.write(f"- **Net Profit:** ${stats['final_equity'] - 10000:,.2f}")
                    
                    # Get trades for equity curve
                    trades_df = backtester.backtest_threshold(threshold)
                    if trades_df is not None:
                        st.subheader("📈 Equity Curve")
                        
                        fig = px.line(trades_df, x='entry_date', y='equity',
                                     title=f"Account Equity Over Time (Threshold: {threshold:,})",
                                     labels={'equity': 'Account Equity ($)', 'entry_date': 'Trade Date'})
                        fig.add_hline(y=10000, line_dash="dash", line_color="gray", 
                                     annotation_text="Starting Capital")
                        fig.update_traces(line=dict(width=3))
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Monthly performance
                        if 'monthly' in stats and stats['monthly']:
                            st.subheader("📅 Monthly Performance")
                            monthly_df = pd.DataFrame(stats['monthly'])
                            monthly_df['year_month'] = monthly_df['year_month'].astype(str)
                            monthly_df['profit_color'] = monthly_df['trade_profit'].apply(
                                lambda x: 'green' if x > 0 else 'red'
                            )
                            
                            fig = px.bar(monthly_df, x='year_month', y='trade_profit',
                                        title="Monthly Profit/Loss ($)",
                                        color='profit_color',
                                        color_discrete_map={'green': '#00CC96', 'red': '#EF553B'})
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"❌ No trades generated with threshold {threshold:,}")
                    st.info("""
                    **Possible reasons:**
                    1. Threshold too extreme (try -30,000 to -60,000)
                    2. Data alignment issue (check Tab 1)
                    3. No COT signals below this threshold
                    """)

# ============================================
# TAB 3: Results
# ============================================
with tab3:
    st.header("📈 Comprehensive Results")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("⚠️ Please load data and run tests in previous tabs first!")
    else:
        if st.session_state.backtester is None:
            st.session_state.backtester = Backtester(
                st.session_state.cot_data,
                st.session_state.price_data
            )
        
        backtester = st.session_state.backtester
        
        st.subheader("🔄 Compare All Thresholds")
        
        if st.button("📊 Run Comprehensive Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing all thresholds (this may take a minute)..."):
                # Test multiple thresholds
                thresholds = [-70000, -60000, -50000, -40000, -30000, -20000, -10000, 0]
                results = []
                
                progress_bar = st.progress(0)
                for i, thresh in enumerate(thresholds):
                    stats = backtester.get_strategy_stats(thresh)
                    if stats:
                        results.append({
                            'Threshold': thresh,
                            'Trades': stats['total_trades'],
                            'Win Rate %': stats['win_rate'],
                            'Profit Factor': stats['profit_factor'],
                            'Total Pips': stats['total_pips'],
                            'Max DD %': stats['max_drawdown_pct'],
                            'Sharpe Ratio': stats['sharpe_ratio'],
                            'Final Equity': stats['final_equity'],
                            'ROI %': stats['roi_pct']
                        })
                    progress_bar.progress((i + 1) / len(thresholds))
                
                if results:
                    results_df = pd.DataFrame(results)
                    
                    # Find best by profit factor
                    best_idx = results_df['Profit Factor'].idxmax()
                    best_row = results_df.loc[best_idx]
                    
                    st.success(f"🏆 **Best Performing Strategy Found!**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info(f"""
                        **Optimal Threshold:** {best_row['Threshold']:,}
                        **Trades:** {best_row['Trades']}
                        **Win Rate:** {best_row['Win Rate %']}%
                        **Profit Factor:** {best_row['Profit Factor']:.2f}
                        """)
                    
                    with col2:
                        st.info(f"""
                        **Performance:**
                        Total Pips: {best_row['Total Pips']:,.1f}
                        Max Drawdown: {best_row['Max DD %']}%
                        Sharpe Ratio: {best_row['Sharpe Ratio']:.2f}
                        ROI: {best_row['ROI %']}%
                        """)
                    
                    # Display comparison table
                    st.subheader("📋 Threshold Comparison Table")
                    
                    # Sort by Profit Factor
                    results_df = results_df.sort_values('Profit Factor', ascending=False)
                    
                    # Format for display
                    display_df = results_df.copy()
                    display_df['Final Equity'] = display_df['Final Equity'].apply(lambda x: f"${x:,.0f}")
                    display_df['ROI %'] = display_df['ROI %'].apply(lambda x: f"{x:.1f}%")
                    display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
                    display_df['Max DD %'] = display_df['Max DD %'].apply(lambda x: f"{x:.1f}%")
                    display_df['Total Pips'] = display_df['Total Pips'].apply(lambda x: f"{x:,.1f}")
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Visualizations
                    st.subheader("📊 Visual Comparisons")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig1 = px.bar(results_df, x='Threshold', y='Profit Factor',
                                     title='Profit Factor by Threshold',
                                     color='Profit Factor',
                                     color_continuous_scale='RdYlGn')
                        fig1.update_layout(yaxis_title="Profit Factor (Higher is Better)")
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    with col2:
                        fig2 = px.bar(results_df, x='Threshold', y='Win Rate %',
                                     title='Win Rate by Threshold',
                                     color='Win Rate %',
                                     color_continuous_scale='RdYlGn')
                        fig2.update_layout(yaxis_title="Win Rate %")
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    # Trade-off chart
                    fig3 = px.scatter(results_df, x='Max DD %', y='Profit Factor',
                                     size='Trades', color='Threshold',
                                     title='Risk-Reward Trade-off: Profit Factor vs Max Drawdown',
                                     hover_data=['Win Rate %', 'Total Pips', 'ROI %'])
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    # Download results
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name="cot_backtesting_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("❌ No valid results from any threshold")
                    st.info("""
                    **Check:**
                    1. Data alignment in Tab 1
                    2. Try different threshold ranges
                    3. Ensure price data covers all COT dates
                    """)

# Footer
st.divider()
st.caption("""
**COT Backtesting Lab v3.0** | Data: 2020-2025 | Strategy: Buy USD/ZAR when Commercial Gold Net < Threshold |
**Note:** Results based on historical data. Includes 3-pip spread costs. Past performance ≠ future results.
""")
