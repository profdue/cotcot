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
    page_title="COT Backtesting Lab",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 COT Backtesting Lab")
st.markdown("**Analyze 6 Years of COT Data | Discover Your Edge**")

# Initialize session state
if 'cot_data' not in st.session_state:
    st.session_state.cot_data = None
if 'backtest_report' not in st.session_state:
    st.session_state.backtest_report = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Data Overview", "🔬 Strategy Analysis", "📈 Performance"])

# TAB 1: Data Overview
with tab1:
    st.header("📊 COT Data Overview (2020-2025)")
    
    if st.button("📂 LOAD ALL COT DATA", type="primary"):
        with st.spinner("Loading 6 years of COT data..."):
            analyzer = COTAnalyzer()
            if analyzer.load_all_cot_data():
                st.session_state.cot_data = analyzer.get_backtest_data()
                st.session_state.analyzer = analyzer
                
                if st.session_state.cot_data is not None:
                    df = st.session_state.cot_data
                    
                    st.success(f"""
                    ✅ **LOADED SUCCESSFULLY!**
                    
                    **Data Summary:**
                    • {len(df)} weekly COT reports
                    • From {df['cot_date'].min().date()} to {df['cot_date'].max().date()}
                    • Commercial Net Range: {df['commercial_net'].min():,} to {df['commercial_net'].max():,}
                    """)
                    
                    # Show data preview
                    with st.expander("📋 Preview Data"):
                        st.dataframe(df.head(10))
                    
                    # Commercial Net over time
                    st.subheader("Commercial Net Position Over Time")
                    fig = px.line(df, x='cot_date', y='commercial_net',
                                 title="Commercial Trader Positioning (Negative = Short Gold)")
                    fig.add_hline(y=-50000, line_dash="dash", line_color="red",
                                 annotation_text="Strong Short Threshold")
                    fig.add_hline(y=50000, line_dash="dash", line_color="green",
                                 annotation_text="Strong Long Threshold")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Distribution
                    st.subheader("Commercial Net Distribution")
                    fig = px.histogram(df, x='commercial_net', nbins=30,
                                      title="How Often Do Different Positions Occur?")
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error("Failed to load data")
            else:
                st.error("No COT files found in data/ folder")

# TAB 2: Strategy Analysis
with tab2:
    st.header("🔬 Strategy Analysis")
    
    if st.session_state.cot_data is None:
        st.warning("Please load data in Tab 1 first!")
    else:
        df = st.session_state.cot_data
        
        st.subheader("Test Different Thresholds")
        
        # Threshold testing
        if st.button("🧪 RUN THRESHOLD ANALYSIS", type="primary"):
            with st.spinner("Testing different thresholds..."):
                backtester = Backtester(df)
                threshold_df = backtester.analyze_thresholds()
                
                if len(threshold_df) > 0:
                    # Find best
                    best_idx = threshold_df['total_pips'].idxmax()
                    best_row = threshold_df.loc[best_idx]
                    
                    st.success(f"""
                    🏆 **BEST THRESHOLD:** {best_row['threshold']:,}
                    
                    **Performance:**
                    • {best_row['trades']} trades
                    • {best_row['win_rate']}% win rate
                    • {best_row['avg_pips']} avg pips per trade
                    • {best_row['total_pips']} total pips
                    """)
                    
                    # Show table
                    st.dataframe(threshold_df.sort_values('total_pips', ascending=False))
                    
                    # Store for later use
                    st.session_state.backtester = backtester
                    st.session_state.best_threshold = best_row['threshold']
                    
                else:
                    st.warning("Not enough data for analysis")
        
        # Detailed analysis for selected threshold
        st.subheader("Detailed Analysis")
        
        threshold = st.slider(
            "Select Threshold to Analyze",
            min_value=-80000,
            max_value=0,
            value=-50000,
            step=5000
        )
        
        if st.button("📊 ANALYZE THIS THRESHOLD"):
            if 'backtester' in st.session_state:
                stats = st.session_state.backtester.get_strategy_stats(threshold)
                
                if stats:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Trades", stats['total_trades'])
                        st.metric("Winning Trades", stats['winning_trades'])
                    
                    with col2:
                        st.metric("Win Rate", f"{stats['win_rate']}%")
                        st.metric("Avg Win (pips)", stats['avg_win'])
                    
                    with col3:
                        st.metric("Profit Factor", stats['profit_factor'])
                        st.metric("Total Pips", stats['total_pips'])
                    
                    # Monthly performance
                    if 'monthly' in stats:
                        monthly_df = pd.DataFrame(stats['monthly'])
                        st.subheader("Monthly Performance")
                        st.dataframe(monthly_df)

# TAB 3: Performance
with tab3:
    st.header("📈 Performance Metrics")
    
    if st.session_state.cot_data is None:
        st.warning("Please load data first!")
    else:
        st.subheader("Strategy Comparison")
        
        # Compare multiple strategies
        thresholds = [-60000, -50000, -40000, -30000]
        
        comparison = []
        for thresh in thresholds:
            backtester = Backtester(st.session_state.cot_data)
            stats = backtester.get_strategy_stats(thresh)
            
            if stats:
                comparison.append({
                    'Threshold': thresh,
                    'Trades': stats['total_trades'],
                    'Win Rate %': stats['win_rate'],
                    'Avg Pips': stats['avg_win'],
                    'Profit Factor': stats['profit_factor'],
                    'Total Pips': stats['total_pips']
                })
        
        if comparison:
            comp_df = pd.DataFrame(comparison)
            st.dataframe(comp_df.sort_values('Total Pips', ascending=False))
            
            # Visualization
            fig = px.bar(comp_df, x='Threshold', y='Win Rate %',
                        title='Win Rate by Threshold')
            st.plotly_chart(fig, use_container_width=True)
        
        # Generate full report
        st.subheader("Full Backtest Report")
        
        if st.button("📄 GENERATE COMPREHENSIVE REPORT"):
            with st.spinner("Generating report..."):
                backtester = Backtester(st.session_state.cot_data)
                report = backtester.generate_report()
                st.session_state.backtest_report = report
                
                if 'error' not in report:
                    st.success("✅ Report Generated!")
                    
                    # Show key findings
                    st.subheader("Key Findings")
                    
                    if 'best_threshold' in report:
                        best = report['best_threshold']
                        st.info(f"""
                        **Optimal Strategy:**
                        • Buy when Commercial Net < {best['threshold']:,}
                        • Expected Win Rate: {best['win_rate']}%
                        • Expected Avg Gain: {best['avg_pips']} pips per trade
                        • Total Historical Pips: {best['total_pips']}
                        """)
                    
                    # Signal distribution
                    if 'signal_distribution' in report:
                        st.subheader("Signal Frequency")
                        for signal, count in report['signal_distribution'].items():
                            if pd.notna(signal):
                                percentage = (count / report['data_overview']['total_weeks']) * 100
                                st.write(f"• **{signal}**: {count} weeks ({percentage:.1f}%)")

# Footer
st.divider()
st.caption("""
**COT Backtesting Lab v1.0** | Data: 2020-2025 | Strategy: Commercial Net Threshold
**Note:** This is for STRATEGY RESEARCH only. All results are simulated.
""")
