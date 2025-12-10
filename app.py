"""
COT STRATEGY LAB - Backtest First, Trade After Proof
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import plotly.graph_objects as go

# Add to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import our new engines
try:
    from data_engine import DataEngine
    from simple_backtester import SimpleBacktester
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    # Create minimal fallbacks
    class DataEngine:
        def __init__(self): pass
    class SimpleBacktester:
        def __init__(self, data): pass

# Page config
st.set_page_config(
    page_title="COT Strategy Lab",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 COT Strategy Lab")
st.markdown("**Step 1: Prove the Strategy | Step 2: Trade with Confidence**")

# Initialize session
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Data Analysis", "🔬 Strategy Testing", "🎯 Live Trade"])

# TAB 1: Data Analysis
with tab1:
    st.header("📊 Step 1: Analyze Your Data")
    
    if st.button("🔄 LOAD & ANALYZE 6 YEARS OF DATA", type="primary"):
        with st.spinner("Loading COT data (2020-2025)..."):
            try:
                # Initialize data engine
                engine = DataEngine()
                
                # Load COT files
                import glob
                cot_files = glob.glob("data/*COT*.csv")
                
                if not cot_files:
                    st.error("No COT files found in data/ folder!")
                else:
                    engine.load_cot_data(cot_files)
                    
                    # Load price data
                    with st.spinner("Loading USD/ZAR price data..."):
                        engine.load_price_data()
                    
                    # Merge data
                    with st.spinner("Merging COT with price data..."):
                        engine.merge_data()
                        engine.save_merged_data()
                    
                    # Get data for backtesting
                    merged_data = engine.get_backtest_data()
                    
                    if merged_data is not None and len(merged_data) > 0:
                        st.session_state.merged_data = merged_data
                        st.session_state.data_loaded = True
                        
                        st.success(f"""
                        ✅ **DATA LOADED SUCCESSFULLY!**
                        
                        **Statistics:**
                        • {len(merged_data)} weeks of trading data
                        • From {merged_data['cot_date'].min().date()} to {merged_data['cot_date'].max().date()}
                        • Average weekly move: {merged_data['pips_change'].mean():.1f} pips
                        • Positive weeks: {(len(merged_data[merged_data['pips_change'] > 0]) / len(merged_data) * 100):.1f}%
                        """)
                        
                        # Show sample data
                        with st.expander("📋 View Sample Data"):
                            st.dataframe(merged_data.head(10))
                            
                    else:
                        st.error("Failed to merge data")
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.data_loaded:
        st.divider()
        st.subheader("📈 Quick Analysis")
        
        merged_data = st.session_state.merged_data
        
        # Basic stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Weeks", len(merged_data))
        with col2:
            positive = len(merged_data[merged_data['pips_change'] > 0])
            st.metric("Positive Weeks", positive, f"{(positive/len(merged_data)*100):.1f}%")
        with col3:
            st.metric("Avg Weekly Pips", f"{merged_data['pips_change'].mean():.1f}")
        with col4:
            st.metric("Std Dev", f"{merged_data['pips_change'].std():.1f}")
        
        # Distribution plot
        st.subheader("Weekly Pips Distribution")
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=merged_data['pips_change'], nbinsx=30))
        fig.update_layout(title="How often do different weekly moves occur?")
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: Strategy Testing
with tab2:
    st.header("🔬 Step 2: Test Trading Strategies")
    
    if not st.session_state.data_loaded:
        st.warning("Please load data in Tab 1 first!")
    else:
        merged_data = st.session_state.merged_data
        
        # Strategy parameters
        st.subheader("Strategy Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            threshold = st.slider(
                "Commercial Net Threshold",
                min_value=-80000,
                max_value=0,
                value=-50000,
                step=5000,
                help="BUY when commercials are MORE short than this"
            )
        
        with col2:
            initial_capital = st.number_input(
                "Initial Capital ($)",
                min_value=50,
                max_value=10000,
                value=100,
                step=50
            )
        
        if st.button("🧪 RUN BACKTEST", type="primary"):
            with st.spinner("Running backtest..."):
                backtester = SimpleBacktester(merged_data)
                
                # Generate report
                report = backtester.generate_report()
                st.session_state.backtest_results = report
                
                # Show threshold analysis
                st.subheader("📊 Threshold Analysis")
                threshold_df = backtester.analyze_thresholds()
                
                if len(threshold_df) > 0:
                    # Find best
                    best_idx = threshold_df['total_pips'].idxmax()
                    best_threshold = threshold_df.loc[best_idx]
                    
                    st.success(f"""
                    🏆 **BEST THRESHOLD FOUND:** {best_threshold['threshold']:,}
                    
                    **Performance:**
                    • {best_threshold['trades']} trades
                    • {best_threshold['win_rate']:.1f}% win rate
                    • {best_threshold['avg_pips']:.1f} avg pips per trade
                    • {best_threshold['total_pips']:.1f} total pips
                    """)
                    
                    # Show table
                    st.dataframe(threshold_df.sort_values('total_pips', ascending=False))
                    
                    # Yearly performance
                    st.subheader("📅 Yearly Performance")
                    yearly_df = pd.DataFrame(report['yearly']).T
                    st.dataframe(yearly_df)
                    
                    # Signal buckets
                    st.subheader("📊 Performance by Signal Strength")
                    buckets_df = pd.DataFrame(report['signal_buckets']).T
                    st.dataframe(buckets_df)
                    
                else:
                    st.warning("Not enough data for threshold analysis")

# TAB 3: Live Trade
with tab3:
    st.header("🎯 Step 3: Live Trade (After Proof)")
    
    if not st.session_state.backtest_results:
        st.info("""
        ⚠️ **Complete Steps 1 & 2 First!**
        
        **Before trading, you need to:**
        1. 📊 **Load & analyze** your 6 years of data
        2. 🔬 **Test strategies** to find what actually works
        3. ✅ **Get statistical proof** of your edge
        
        Only then should you consider live trading.
        """)
    else:
        st.success("""
        ✅ **BACKTEST COMPLETE!**
        
        Now you can trade with **confidence**, not hope.
        """)
        
        # Show today's signal with historical context
        st.subheader("📈 Today's Signal with Historical Context")
        
        # Get latest COT signal
        latest_cot = st.session_state.merged_data.iloc[-1]
        commercial_net = latest_cot['commercial_net']
        
        # Find which bucket this falls into
        buckets_df = pd.DataFrame(st.session_state.backtest_results['signal_buckets']).T
        
        # Determine signal strength
        if commercial_net < -60000:
            strength = "Extreme Short"
        elif commercial_net < -40000:
            strength = "Strong Short"
        elif commercial_net < -20000:
            strength = "Moderate Short"
        else:
            strength = "Mild Short"
        
        # Get historical performance for this strength
        if strength in buckets_df.index:
            hist_perf = buckets_df.loc[strength]
            
            st.info(f"""
            **Current Signal:** Commercials SHORT {abs(commercial_net):,}
            **Signal Strength:** {strength}
            
            **Historical Performance (Similar Signals):**
            • {hist_perf['weeks']} past occurrences
            • {hist_perf['win_rate']:.1f}% win rate
            • {hist_perf['avg_pips']:.1f} average pips
            """)
        
        # Market input
        st.subheader("📊 Today's Market Levels")
        col1, col2 = st.columns(2)
        with col1:
            today_support = st.number_input("Support Level", value=17.0433, format="%.4f")
        with col2:
            today_resistance = st.number_input("Resistance Level", value=17.0590, format="%.4f")
        
        if st.button("🎯 GENERATE OPTIMIZED TRADE", type="primary"):
            # Based on backtest results, generate optimal trade
            best_threshold = st.session_state.backtest_results.get('best_threshold', {})
            
            if best_threshold:
                st.success(f"""
                🎯 **OPTIMIZED TRADE PLAN**
                
                **Based on {best_threshold.get('trades', 0)} historical trades:**
                • Signal: BUY USD/ZAR (Commercials < {best_threshold.get('threshold', -50000):,})
                • Entry: {today_support + 0.0010:.4f} (just above support)
                • Stop: {today_support - 0.0022:.4f} (22 pips - optimized)
                • Target: {today_support + 0.0048:.4f} (48 pips - 2.18:1 R:R)
                • Position: 0.01 lots
                • Risk: $0.50 (0.5% of $100)
                
                **Expected Performance:**
                • Win Rate: {best_threshold.get('win_rate', 0):.1f}%
                • Avg Gain: {best_threshold.get('avg_pips', 0):.1f} pips
                • Expected Value: +{(best_threshold.get('avg_pips', 0) * 0.10):.2f} per trade
                """)

# Footer
st.divider()
st.caption("""
**COT Strategy Lab v1.0** | Data-Driven Trading | 6-Year Historical Analysis
**Remember:** Trade based on proof, not hope. Your data is your edge.
""")
