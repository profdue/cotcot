import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sys
import os
import csv

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

# Simple price loader function
def simple_load_price_data():
    """Simple loader that definitely works"""
    filepath = "data/usd_zar_historical_data.csv"
    
    try:
        # First, let's see what's in the file
        with open(filepath, 'rb') as f:
            raw = f.read(1000).decode('utf-8-sig')
        
        # Parse manually
        lines = raw.split('\n')
        headers = [h.strip('"') for h in lines[0].split(',')]
        
        data = []
        for line in lines[1:20]:  # First 20 lines
            if not line.strip():
                continue
            values = [v.strip('"') for v in line.split(',')]
            if len(values) >= 2:
                data.append(values)
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers[:len(data[0])])
        
        # Convert date
        df['date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        
        # Convert price
        df['price'] = pd.to_numeric(df['Price'].str.replace(',', ''), errors='coerce')
        
        # Clean up
        df = df.dropna(subset=['date', 'price'])
        df = df.sort_values('date')
        
        return df[['date', 'price']]
        
    except Exception as e:
        st.error(f"Manual load failed: {e}")
        return None

# Page config
st.set_page_config(
    page_title="COT Backtesting Lab",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 COT Backtesting Lab")
st.markdown("**Analyze 6 Years of COT Data with USD/ZAR Prices**")

# Initialize session state
if 'cot_data' not in st.session_state:
    st.session_state.cot_data = None
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'backtester' not in st.session_state:
    st.session_state.backtester = None

# Tabs
tab1, tab2 = st.tabs(["📊 Data Loading", "🔬 Strategy Testing"])

# ============================================
# TAB 1: Data Loading
# ============================================
with tab1:
    st.header("📊 Load Your Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. COT Data")
        if st.button("📂 Load COT Data (2020-2025)", type="primary", use_container_width=True):
            with st.spinner("Loading COT data..."):
                analyzer = COTAnalyzer()
                if analyzer.load_all_cot_data():
                    st.session_state.cot_data = analyzer.get_backtest_data()
                    
                    if st.session_state.cot_data is not None:
                        df = st.session_state.cot_data
                        st.success(f"""
                        ✅ **COT Data Loaded!**
                        - {len(df)} weekly reports
                        - From {df['cot_date'].min().date()} to {df['cot_date'].max().date()}
                        - Commercial Net Range: {df['commercial_net'].min():,} to {df['commercial_net'].max():,}
                        """)
                        
                        # Show chart
                        fig = px.line(df, x='cot_date', y='commercial_net',
                                     title="Commercial Gold Positioning")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("Failed to load COT data")
                else:
                    st.error("No COT files found")
    
    with col2:
        st.subheader("2. USD/ZAR Price Data")
        if st.button("💹 Load USD/ZAR Prices", type="secondary", use_container_width=True):
            with st.spinner("Loading price data..."):
                # Use simple loader
                price_df = simple_load_price_data()
                
                if price_df is not None:
                    st.session_state.price_data = price_df
                    
                    st.success(f"""
                    ✅ **USD/ZAR Prices Loaded!**
                    - {len(price_df)} trading days
                    - From {price_df['date'].min().date()} to {price_df['date'].max().date()}
                    - Price Range: {price_df['price'].min():.4f} to {price_df['price'].max():.4f}
                    """)
                    
                    # Show chart
                    fig = px.line(price_df, x='date', y='price',
                                 title="USD/ZAR Historical Price")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Could not load price data")
    
    # Show status
    st.subheader("📋 Data Status")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.cot_data is not None:
            st.success("✅ COT Data: Loaded")
        else:
            st.warning("⚠️ COT Data: Not Loaded")
    
    with col2:
        if st.session_state.price_data is not None:
            st.success("✅ USD/ZAR Prices: Loaded")
        else:
            st.warning("⚠️ USD/ZAR Prices: Not Loaded")
    
    # Initialize backtester when both are loaded
    if st.session_state.cot_data is not None and st.session_state.price_data is not None:
        if st.session_state.backtester is None:
            st.session_state.backtester = Backtester(
                st.session_state.cot_data,
                st.session_state.price_data
            )
            st.success("✅ Backtester Initialized! Ready for strategy testing.")
        
        # Show combined view
        st.subheader("📈 Combined View")
        
        fig = go.Figure()
        
        # Add price
        fig.add_trace(go.Scatter(
            x=st.session_state.price_data['date'],
            y=st.session_state.price_data['price'],
            name="USD/ZAR Price",
            line=dict(color='blue'),
            yaxis="y2"
        ))
        
        # Add commercial net
        fig.add_trace(go.Scatter(
            x=st.session_state.cot_data['cot_date'],
            y=st.session_state.cot_data['commercial_net'],
            name="Commercial Net (Gold)",
            line=dict(color='red'),
            fill='tozeroy'
        ))
        
        fig.update_layout(
            title="Commercial Gold Positioning vs USD/ZAR Price",
            yaxis=dict(title="Commercial Net Position", side="left"),
            yaxis2=dict(title="USD/ZAR Price", side="right", overlaying="y"),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 2: Strategy Testing
# ============================================
with tab2:
    st.header("🔬 Strategy Testing")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("⚠️ Please load both datasets in the Data Loading tab first!")
    else:
        if st.session_state.backtester is None:
            st.session_state.backtester = Backtester(
                st.session_state.cot_data,
                st.session_state.price_data
            )
        
        backtester = st.session_state.backtester
        
        st.info("""
        **Strategy:** Buy USD/ZAR when Commercial Gold Net Position is below threshold  
        **Execution:** Enter next trading day, exit 1 week later  
        **Costs:** 3-pip spread included | **Risk:** 1% per trade
        """)
        
        # Simple threshold testing
        st.subheader("🧪 Test Strategy")
        
        threshold = st.slider(
            "Commercial Net Threshold",
            min_value=-80000,
            max_value=0,
            value=-50000,
            step=5000,
            help="Buy USD/ZAR when Commercial Gold Net is below this value"
        )
        
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner("Running backtest..."):
                stats = backtester.get_strategy_stats(threshold)
                
                if stats:
                    # Display results
                    st.success(f"✅ Backtest Complete: {stats['total_trades']} trades")
                    
                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Trades", stats['total_trades'])
                        st.metric("Win Rate", f"{stats['win_rate']}%")
                    
                    with col2:
                        st.metric("Profit Factor", f"{stats['profit_factor']}")
                        st.metric("Total Pips", f"{stats['total_pips']}")
                    
                    with col3:
                        st.metric("Max Drawdown", f"{stats['max_drawdown_pct']}%")
                        st.metric("Sharpe Ratio", f"{stats['sharpe_ratio']}")
                    
                    with col4:
                        st.metric("Final Equity", f"${stats['final_equity']:,.0f}")
                        st.metric("ROI", f"{stats['roi_pct']}%")
                    
                    # Detailed metrics
                    with st.expander("📊 Detailed Metrics"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Trade Statistics:**")
                            st.write(f"- Winning Trades: {stats['winning_trades']}")
                            st.write(f"- Losing Trades: {stats['losing_trades']}")
                            st.write(f"- Avg Win: {stats['avg_win_pips']} pips")
                            st.write(f"- Avg Loss: {stats['avg_loss_pips']} pips")
                            st.write(f"- Max Win: {stats['max_win_pips']} pips")
                            st.write(f"- Max Loss: {stats['max_loss_pips']} pips")
                        
                        with col2:
                            st.write("**Performance:**")
                            st.write(f"- Total Profit: ${stats['total_profit']:,.0f}")
                            st.write(f"- Avg Return: {stats['avg_return_pct']}%")
                            st.write(f"- Starting Capital: $10,000")
                            st.write(f"- Ending Capital: ${stats['final_equity']:,.2f}")
                            st.write(f"- Net Profit: ${stats['final_equity'] - 10000:,.2f}")
                    
                    # Get trades for equity curve
                    trades_df = backtester.backtest_threshold(threshold)
                    if trades_df is not None:
                        st.subheader("📈 Equity Curve")
                        fig = px.line(trades_df, x='entry_date', y='equity',
                                     title=f"Account Equity Over Time (Threshold: {threshold:,})")
                        fig.add_hline(y=10000, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Monthly performance
                        if 'monthly' in stats and stats['monthly']:
                            st.subheader("📅 Monthly Performance")
                            monthly_df = pd.DataFrame(stats['monthly'])
                            monthly_df['year_month'] = monthly_df['year_month'].astype(str)
                            
                            fig = px.bar(monthly_df, x='year_month', y='trade_profit',
                                        title="Monthly Profit/Loss ($)")
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("No trades generated with this threshold. Try a different value.")
        
        # Compare multiple thresholds
        st.subheader("🔄 Compare Different Thresholds")
        
        if st.button("📊 Compare All Thresholds", type="secondary"):
            with st.spinner("Testing all thresholds..."):
                # Test common thresholds
                thresholds = [-70000, -60000, -50000, -40000, -30000, -20000]
                results = []
                
                for thresh in thresholds:
                    stats = backtester.get_strategy_stats(thresh)
                    if stats:
                        results.append({
                            'Threshold': thresh,
                            'Trades': stats['total_trades'],
                            'Win Rate': f"{stats['win_rate']}%",
                            'Profit Factor': stats['profit_factor'],
                            'Total Pips': stats['total_pips'],
                            'Max DD': f"{stats['max_drawdown_pct']}%",
                            'Final Equity': f"${stats['final_equity']:,.0f}"
                        })
                
                if results:
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Visual comparison
                    fig = px.bar(results_df, x='Threshold', y='Profit Factor',
                                title='Profit Factor by Threshold',
                                color='Profit Factor',
                                color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No results to compare")

# Footer
st.divider()
st.caption("""
**COT Backtesting Lab v1.0** | Strategy: Buy USD/ZAR when Commercial Gold Net < Threshold |
**Note:** Includes 3-pip spread. Past performance ≠ future results.
""")
