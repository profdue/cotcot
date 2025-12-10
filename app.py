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
        def __init__(self, data=None, price_data=None):
            self.cot_data = data.copy() if data is not None else None
            self.price_data = price_data.copy() if price_data is not None else None
        def get_strategy_stats(self, threshold): return None

# Custom price loader
def load_price_data_custom():
    """Load USD/ZAR prices with DD/MM/YYYY format"""
    try:
        filepath = "data/usd_zar_historical_data.csv"
        
        # Read with pandas
        df = pd.read_csv(
            filepath,
            encoding='utf-8-sig',
            quotechar='"',
            thousands=',',
            engine='python'
        )
        
        # Clean column names
        df.columns = [col.strip().replace('"', '') for col in df.columns]
        
        # Find columns
        date_col = 'Date' if 'Date' in df.columns else df.columns[0]
        price_col = 'Price' if 'Price' in df.columns else df.columns[1]
        
        # Parse dates - handle DD/MM/YYYY
        df['date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        
        # Convert price
        df['price'] = pd.to_numeric(
            df[price_col].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
        
        # Clean and sort
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
tab1, tab2 = st.tabs(["📊 Data Loading", "🔬 Backtesting"])

# ============================================
# TAB 1: Data Loading
# ============================================
with tab1:
    st.header("📊 Load Your Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📂 Load COT Data", type="primary", use_container_width=True):
            with st.spinner("Loading COT data..."):
                analyzer = COTAnalyzer()
                if analyzer.load_all_cot_data():
                    st.session_state.cot_data = analyzer.get_backtest_data()
                    df = st.session_state.cot_data
                    
                    st.success(f"✅ COT Data Loaded: {len(df)} weeks")
                    
                    # Show chart
                    fig = px.line(df, x='cot_date', y='commercial_net',
                                 title="Commercial Gold Positioning")
                    st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if st.button("💹 Load USD/ZAR Prices", type="secondary", use_container_width=True):
            with st.spinner("Loading price data..."):
                price_df = load_price_data_custom()
                
                if price_df is not None:
                    st.session_state.price_data = price_df
                    st.success(f"✅ USD/ZAR Prices Loaded: {len(price_df)} days")
                    
                    # Show chart
                    fig = px.line(price_df, x='date', y='price',
                                 title="USD/ZAR Historical Price")
                    st.plotly_chart(fig, use_container_width=True)
    
    # Show status
    st.subheader("📋 Data Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.cot_data is not None:
            df = st.session_state.cot_data
            st.success(f"✅ COT Data: {len(df)} weeks")
            st.write(f"Date Range: {df['cot_date'].min().date()} to {df['cot_date'].max().date()}")
        else:
            st.warning("⚠️ COT Data: Not Loaded")
    
    with col2:
        if st.session_state.price_data is not None:
            df = st.session_state.price_data
            st.success(f"✅ USD/ZAR Prices: {len(df)} days")
            st.write(f"Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
        else:
            st.warning("⚠️ USD/ZAR Prices: Not Loaded")
    
    # Combined view when both loaded
    if st.session_state.cot_data is not None and st.session_state.price_data is not None:
        st.subheader("📈 Combined View")
        
        # Create a simple combined chart
        fig = go.Figure()
        
        # Add price (right axis)
        price_df = st.session_state.price_data
        fig.add_trace(go.Scatter(
            x=price_df['date'],
            y=price_df['price'],
            name="USD/ZAR Price",
            line=dict(color='blue'),
            yaxis="y2"
        ))
        
        # Add commercial net (left axis)
        cot_df = st.session_state.cot_data
        fig.add_trace(go.Scatter(
            x=cot_df['cot_date'],
            y=cot_df['commercial_net'],
            name="Commercial Net (Gold)",
            line=dict(color='red'),
            fill='tozeroy'
        ))
        
        # SIMPLIFIED LAYOUT - No complex formatting that causes errors
        fig.update_layout(
            title="Commercial Gold vs USD/ZAR Price",
            yaxis=dict(title="Commercial Net", side="left"),
            yaxis2=dict(title="USD/ZAR Price", side="right", overlaying="y"),
            hovermode='x'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 2: Backtesting
# ============================================
with tab2:
    st.header("🔬 Strategy Backtesting")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("Please load both datasets first!")
    else:
        # Initialize backtester
        backtester = Backtester(
            st.session_state.cot_data,
            st.session_state.price_data
        )
        
        st.info("**Strategy:** Buy USD/ZAR when Commercial Gold Net < Threshold")
        
        # Test single threshold
        st.subheader("Test Single Threshold")
        
        threshold = st.slider(
            "Select Threshold",
            min_value=-150000,
            max_value=0,
            value=-50000,
            step=10000
        )
        
        if st.button("Run Backtest", type="primary"):
            stats = backtester.get_strategy_stats(threshold)
            
            if stats:
                # Show results
                st.success(f"✅ {stats['total_trades']} trades generated")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", stats['total_trades'])
                    st.metric("Win Rate", f"{stats['win_rate']}%")
                
                with col2:
                    st.metric("Profit Factor", f"{stats['profit_factor']:.2f}")
                    st.metric("Total Pips", f"{stats['total_pips']:,.0f}")
                
                with col3:
                    st.metric("Max Drawdown", f"{stats['max_drawdown_pct']}%")
                    st.metric("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
                
                with col4:
                    st.metric("Final Equity", f"${stats['final_equity']:,.0f}")
                    st.metric("ROI", f"{stats['roi_pct']}%")
                
                # Equity curve
                trades_df = backtester.backtest_threshold(threshold)
                if trades_df is not None:
                    fig = px.line(trades_df, x='entry_date', y='equity',
                                 title="Equity Curve")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No trades generated. Try a different threshold.")
        
        # Compare thresholds
        st.subheader("Compare Multiple Thresholds")
        
        if st.button("Compare All Thresholds"):
            thresholds = [-70000, -60000, -50000, -40000, -30000, -20000]
            results = []
            
            for thresh in thresholds:
                stats = backtester.get_strategy_stats(thresh)
                if stats:
                    results.append({
                        'Threshold': thresh,
                        'Trades': stats['total_trades'],
                        'Win Rate %': stats['win_rate'],
                        'Profit Factor': stats['profit_factor'],
                        'Total Pips': stats['total_pips'],
                        'Max DD %': stats['max_drawdown_pct']
                    })
            
            if results:
                results_df = pd.DataFrame(results)
                results_df = results_df.sort_values('Profit Factor', ascending=False)
                st.dataframe(results_df, use_container_width=True)
                
                # Chart
                fig = px.bar(results_df, x='Threshold', y='Profit Factor',
                            title='Profit Factor by Threshold')
                st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.caption("**COT Backtesting Lab v1.0** | Data: 2020-2025")
