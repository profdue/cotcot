import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
        def __init__(self): pass
    class Backtester:
        def __init__(self, data): pass

# Page config
st.set_page_config(
    page_title="COT Backtesting Lab - REAL DATA",
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

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Data Overview", "🔬 Strategy Analysis", "📈 Performance"])

# TAB 1: Data Overview
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
                        """)
    
    with col2:
        if st.button("💹 LOAD USD/ZAR PRICES", type="secondary", use_container_width=True):
            with st.spinner("Loading USD/ZAR historical data..."):
                try:
                    price_df = pd.read_csv("data/usd_zar_historical_data.csv", delimiter='\t')
                    price_df['date'] = pd.to_datetime(price_df['Date'], dayfirst=True)
                    
                    # Clean price column
                    price_df['price'] = pd.to_numeric(price_df['Price'].astype(str).str.replace(',', ''), errors='coerce')
                    
                    st.session_state.price_data = price_df
                    
                    st.success(f"""
                    ✅ **USD/ZAR DATA LOADED!**
                    
                    **Price Summary:**
                    • {len(price_df)} trading days
                    • From {price_df['date'].min().date()} to {price_df['date'].max().date()}
                    • Price Range: {price_df['price'].min():.4f} to {price_df['price'].max():.4f}
                    • Current: {price_df['price'].iloc[-1]:.4f}
                    """)
                    
                    # Show price chart
                    fig = px.line(price_df, x='date', y='price',
                                 title="USD/ZAR Historical Price")
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error loading price data: {e}")
    
    # Show combined data if both loaded
    if st.session_state.cot_data is not None and st.session_state.price_data is not None:
        st.subheader("📈 Combined Data Analysis")
        
        # Commercial Net over time with price overlay
        fig = go.Figure()
        
        # Add price (secondary axis)
        fig.add_trace(go.Scatter(
            x=st.session_state.price_data['date'],
            y=st.session_state.price_data['price'],
            name="USD/ZAR Price",
            line=dict(color='blue'),
            yaxis="y2"
        ))
        
        # Add commercial net (primary axis)
        fig.add_trace(go.Scatter(
            x=st.session_state.cot_data['cot_date'],
            y=st.session_state.cot_data['commercial_net'],
            name="Commercial Net",
            line=dict(color='red'),
            fill='tozeroy'
        ))
        
        fig.update_layout(
            title="Commercial Positioning vs USD/ZAR Price",
            yaxis=dict(title="Commercial Net Position", side="left"),
            yaxis2=dict(title="USD/ZAR Price", side="right", overlaying="y"),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: Strategy Analysis
with tab2:
    st.header("🔬 Strategy Analysis with REAL Prices")
    
    if st.session_state.cot_data is None:
        st.warning("Please load COT data in Tab 1 first!")
    elif st.session_state.price_data is None:
        st.warning("Please load USD/ZAR price data in Tab 1 first!")
    else:
        # Initialize backtester with BOTH datasets
        backtester = Backtester(st.session_state.cot_data, st.session_state.price_data)
        
        st.subheader("Test Different Thresholds")
        
        if st.button("🧪 RUN REAL BACKTEST", type="primary"):
            with st.spinner("Running backtest with actual prices..."):
                threshold_df = backtester.analyze_thresholds()
                
                if len(threshold_df) > 0:
                    # Find best
                    best_idx = threshold_df['total_pips'].idxmax()
                    best_row = threshold_df.loc[best_idx]
                    
                    st.success(f"""
                    🏆 **OPTIMAL STRATEGY FOUND!**
                    
                    **Threshold:** {best_row['threshold']:,}
                    **Trades:** {best_row['trades']}
                    **Win Rate:** {best_row['win_rate']}%
                    **Total Pips:** {best_row['total_pips']}
                    **Profit Factor:** {best_row['profit_factor']}
                    """)
                    
                    # Show detailed table
                    st.dataframe(threshold_df.sort_values('total_pips', ascending=False))
                    
                    # Store for later use
                    st.session_state.backtester = backtester
                    st.session_state.best_threshold = best_row['threshold']
                    
                    # Show equity curve for best threshold
                    trades_df = backtester.backtest_threshold(best_row['threshold'])
                    if trades_df is not None:
                        fig = px.line(trades_df, x='entry_date', y='cumulative_profit',
                                     title="Equity Curve (Starting with $10,000)")
                        fig.add_hline(y=0, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed analysis for selected threshold
        st.subheader("📊 Analyze Specific Threshold")
        
        threshold = st.slider(
            "Select Commercial Net Threshold",
            min_value=-80000,
            max_value=0,
            value=-50000,
            step=5000
        )
        
        if st.button("📈 ANALYZE SELECTED THRESHOLD"):
            if 'backtester' in st.session_state:
                stats = st.session_state.backtester.get_strategy_stats(threshold)
                
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Trades", stats['total_trades'])
                        st.metric("Win Rate", f"{stats['win_rate']}%")
                    
                    with col2:
                        st.metric("Profit Factor", stats['profit_factor'])
                        st.metric("Max Drawdown", f"{stats['max_drawdown_pct']}%")
                    
                    with col3:
                        st.metric("Total Pips", stats['total_pips'])
                        st.metric("Avg Return", f"{stats['avg_return_pct']}%")
                    
                    with col4:
                        st.metric("Final Equity", f"${stats['final_equity']:,.2f}")
                        st.metric("Avg Win (pips)", stats['avg_win'])
                    
                    # Monthly performance
                    if 'monthly' in stats and stats['monthly']:
                        monthly_df = pd.DataFrame(stats['monthly'])
                        st.subheader("Monthly Performance (Pips)")
                        st.dataframe(monthly_df)

# TAB 3: Performance
with tab3:
    st.header("📈 Performance Metrics & Comparison")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("Please load both datasets in Tab 1 first!")
    else:
        backtester = Backtester(st.session_state.cot_data, st.session_state.price_data)
        
        st.subheader("Strategy Comparison")
        
        thresholds = [-60000, -50000, -40000, -30000, -20000]
        
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
                    'Final Equity': f"${stats['final_equity']:,.0f}"
                })
        
        if comparison:
            comp_df = pd.DataFrame(comparison)
            st.dataframe(comp_df.sort_values('Total Pips', ascending=False))
            
            # Visual comparison
            fig1 = px.bar(comp_df, x='Threshold', y='Win Rate %',
                         title='Win Rate by Threshold')
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.bar(comp_df, x='Threshold', y='Total Pips',
                         title='Total Pips by Threshold')
            st.plotly_chart(fig2, use_container_width=True)
        
        # Generate full report
        st.subheader("📄 Full Backtest Report")
        
        if st.button("📊 GENERATE COMPREHENSIVE REPORT"):
            with st.spinner("Generating detailed report..."):
                report = backtester.generate_report()
                st.session_state.backtest_report = report
                
                if 'error' not in report:
                    st.success("✅ Real Data Report Generated!")
                    
                    # Show key findings
                    st.subheader("🔑 Key Findings from Real Data")
                    
                    if 'best_threshold' in report:
                        best = report['best_threshold']
                        st.info(f"""
                        **Optimal Strategy (Based on 6 Years of Data):**
                        • **Entry Signal:** Commercial Net < {best['threshold']:,}
                        • **Expected Win Rate:** {best['win_rate']}%
                        • **Average Trade:** {best['avg_pips']} pips
                        • **Total Historical Profit:** {best['total_pips']} pips
                        • **Profit Factor:** {best['profit_factor']}
                        """)
                    
                    # Data statistics
                    if 'data_overview' in report:
                        data = report['data_overview']
                        st.subheader("📊 Data Statistics")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**COT Reports:** {data['total_cot_weeks']}")
                            st.write(f"**Price Days:** {data['total_price_days']}")
                            st.write(f"**Avg Commercial Net:** {data['avg_commercial_net']:,.0f}")
                        
                        with col2:
                            st.write(f"**USD/ZAR Volatility:** {data['usdzar_volatility']}% annual")
                            st.write(f"**Avg USD/ZAR Price:** {data['avg_usdzar_price']}")
                            st.write(f"**Commercial Net Range:** {data['min_commercial_net']:,} to {data['max_commercial_net']:,}")

# Footer
st.divider()
st.caption("""
**COT Backtesting Lab v2.0 - REAL DATA EDITION** | 
COT Data: 2020-2025 | USD/ZAR Prices: 2020-2025 |
Strategy: Buy USD/ZAR when Commercial Gold Net < Threshold |
**Note:** Includes 3-pip spread cost. Past performance ≠ future results.
""")
