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

# Page config
st.set_page_config(
    page_title="COT Strategy Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 COT Strategy Analyzer")
st.markdown("**Commercial Gold Positioning → USD/ZAR Trading Strategy**")

# Initialize session state
if 'cot_data' not in st.session_state:
    st.session_state.cot_data = None
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Data", "🎯 Strategy", "📊 Results", "⚡ Optimization"])

# ============================================
# TAB 1: Data
# ============================================
with tab1:
    st.header("📈 Data Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📂 Load COT Data", type="primary", use_container_width=True):
            with st.spinner("Loading..."):
                analyzer = COTAnalyzer()
                if analyzer.load_all_cot_data():
                    st.session_state.cot_data = analyzer.get_backtest_data()
                    st.success("✅ COT Data Loaded")
    
    with col2:
        if st.button("💹 Load USD/ZAR Prices", type="secondary", use_container_width=True):
            with st.spinner("Loading..."):
                try:
                    df = pd.read_csv(
                        "data/usd_zar_historical_data.csv",
                        encoding='utf-8-sig',
                        quotechar='"',
                        thousands=','
                    )
                    df.columns = [col.strip().replace('"', '') for col in df.columns]
                    df['date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                    df['price'] = pd.to_numeric(df['Price'].astype(str).str.replace(',', ''), errors='coerce')
                    df = df.dropna(subset=['date', 'price'])
                    df = df.sort_values('date')
                    st.session_state.price_data = df[['date', 'price']]
                    st.success("✅ Price Data Loaded")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Display loaded data
    if st.session_state.cot_data is not None:
        df = st.session_state.cot_data
        st.subheader("📋 COT Data Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Weeks", len(df))
            st.metric("Date Range", f"{df['cot_date'].min().date()} to {df['cot_date'].max().date()}")
        with col2:
            st.metric("Avg Commercial Net", f"{df['commercial_net'].mean():,.0f}")
            st.metric("Min Commercial Net", f"{df['commercial_net'].min():,.0f}")
        with col3:
            st.metric("Max Commercial Net", f"{df['commercial_net'].max():,.0f}")
            st.metric("Current", f"{df['commercial_net'].iloc[-1]:,.0f}")
        
        # Commercial net chart
        fig = px.line(df, x='cot_date', y='commercial_net', 
                     title="Commercial Net Position Over Time")
        st.plotly_chart(fig, use_container_width=True)
    
    if st.session_state.price_data is not None:
        df = st.session_state.price_data
        st.subheader("📋 USD/ZAR Data Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Days", len(df))
            st.metric("Date Range", f"{df['date'].min().date()} to {df['date'].max().date()}")
        with col2:
            st.metric("Min Price", f"{df['price'].min():.4f}")
            st.metric("Max Price", f"{df['price'].max():.4f}")
        with col3:
            st.metric("Current Price", f"{df['price'].iloc[-1]:.4f}")
            st.metric("6-Year Change", f"{((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0] * 100):.1f}%")
        
        # Price chart
        fig = px.line(df, x='date', y='price', title="USD/ZAR Price History")
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# TAB 2: Strategy
# ============================================
with tab2:
    st.header("🎯 Trading Strategy")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("Please load data first in the Data tab.")
    else:
        st.info("""
        **Strategy Rules:**
        1. **Signal:** When Commercial Gold Net Position < Threshold
        2. **Action:** Buy USD/ZAR (Go Long)
        3. **Entry:** Next trading day after COT report (Tuesday)
        4. **Exit:** 1 week later (next COT report date)
        5. **Costs:** 3-pip spread included
        6. **Position Size:** $10,000 account, 1% risk per trade
        """)
        
        # Initialize backtester
        backtester = Backtester(
            st.session_state.cot_data,
            st.session_state.price_data
        )
        
        st.subheader("🧪 Test Strategy")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            threshold = st.slider(
                "Commercial Net Threshold",
                min_value=-150000,
                max_value=0,
                value=-30000,
                step=5000,
                help="Lower threshold = more conservative (fewer trades)"
            )
        
        with col2:
            st.metric("Selected Threshold", f"{threshold:,}")
        
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner("Running backtest..."):
                stats = backtester.get_strategy_stats(threshold)
                
                if stats:
                    st.session_state.current_stats = stats
                    st.session_state.current_threshold = threshold
                    
                    st.success(f"✅ Generated {stats['total_trades']} trades")
                    
                    # Display metrics
                    st.subheader("📊 Performance Metrics")
                    
                    # Key metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Trades", stats['total_trades'])
                        st.metric("Win Rate", f"{stats['win_rate']}%")
                    
                    with col2:
                        st.metric("Profit Factor", f"{stats['profit_factor']:.2f}")
                        color = "green" if stats['profit_factor'] > 1.5 else "orange" if stats['profit_factor'] > 1.2 else "red"
                        st.markdown(f"<span style='color:{color}'>• >1.5: Excellent<br>• 1.2-1.5: Good<br>• <1.2: Poor</span>", unsafe_allow_html=True)
                    
                    with col3:
                        st.metric("Total Pips", f"{stats['total_pips']:,.0f}")
                        st.metric("Avg Trade", f"{stats['total_pips']/stats['total_trades']:.0f} pips")
                    
                    with col4:
                        st.metric("Max Drawdown", f"{stats['max_drawdown_pct']}%")
                        color = "green" if stats['max_drawdown_pct'] > -20 else "orange" if stats['max_drawdown_pct'] > -40 else "red"
                        st.markdown(f"<span style='color:{color}'>• <-20%: Good<br>• -20 to -40%: Acceptable<br>• >-40%: Risky</span>", unsafe_allow_html=True)
                    
                    # Additional metrics
                    st.subheader("📈 Detailed Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Trade Statistics:**")
                        st.write(f"- Winning Trades: {stats['winning_trades']}")
                        st.write(f"- Losing Trades: {stats['losing_trades']}")
                        st.write(f"- Avg Win: {stats['avg_win_pips']} pips")
                        st.write(f"- Avg Loss: {stats['avg_loss_pips']} pips")
                        st.write(f"- Risk/Reward Ratio: {abs(stats['avg_win_pips']/stats['avg_loss_pips']):.2f}")
                    
                    with col2:
                        st.write("**Financial Results:**")
                        st.write(f"- Starting Capital: $10,000")
                        st.write(f"- Final Equity: ${stats['final_equity']:,.0f}")
                        st.write(f"- Net Profit: ${stats['final_equity'] - 10000:,.0f}")
                        st.write(f"- ROI: {stats['roi_pct']}%")
                        st.write(f"- Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
                    
                    # Equity curve
                    trades_df = backtester.backtest_threshold(threshold)
                    if trades_df is not None:
                        st.subheader("💰 Equity Curve")
                        fig = px.line(trades_df, x='entry_date', y='equity',
                                     title=f"Account Growth (Threshold: {threshold:,})",
                                     labels={'equity': 'Account Value ($)', 'entry_date': 'Date'})
                        fig.add_hline(y=10000, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Drawdown chart
                        trades_df['peak'] = trades_df['equity'].expanding().max()
                        trades_df['drawdown'] = (trades_df['equity'] - trades_df['peak']) / trades_df['peak'] * 100
                        
                        fig2 = px.area(trades_df, x='entry_date', y='drawdown',
                                      title="Drawdown Over Time",
                                      labels={'drawdown': 'Drawdown (%)', 'entry_date': 'Date'})
                        fig2.update_traces(line=dict(color='red'), fillcolor='rgba(255,0,0,0.3)')
                        st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.error("No trades generated. Try a higher threshold (closer to zero).")

# ============================================
# TAB 3: Results
# ============================================
with tab3:
    st.header("📊 Strategy Comparison")
    
    if st.session_state.cot_data is None or st.session_state.price_data is None:
        st.warning("Please load data first.")
    else:
        backtester = Backtester(
            st.session_state.cot_data,
            st.session_state.price_data
        )
        
        if st.button("📈 Compare All Thresholds", type="primary"):
            with st.spinner("Testing multiple thresholds..."):
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
                            'Sharpe': stats['sharpe_ratio'],
                            'ROI %': stats['roi_pct'],
                            'Final Equity': stats['final_equity']
                        })
                    progress_bar.progress((i + 1) / len(thresholds))
                
                if results:
                    results_df = pd.DataFrame(results)
                    st.session_state.backtest_results = results_df
                    
                    # Find best strategies
                    best_pf_idx = results_df['Profit Factor'].idxmax()
                    best_pf = results_df.loc[best_pf_idx]
                    
                    best_sharpe_idx = results_df['Sharpe'].idxmax()
                    best_sharpe = results_df.loc[best_sharpe_idx]
                    
                    # Display findings
                    st.subheader("🎯 Best Performing Strategies")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.success(f"**🏆 Best Profit Factor:**")
                        st.write(f"Threshold: {best_pf['Threshold']:,}")
                        st.write(f"Profit Factor: {best_pf['Profit Factor']:.2f}")
                        st.write(f"Trades: {best_pf['Trades']}")
                        st.write(f"Win Rate: {best_pf['Win Rate %']}%")
                        st.write(f"Total Pips: {best_pf['Total Pips']:,.0f}")
                    
                    with col2:
                        st.success(f"**📈 Best Risk-Adjusted:**")
                        st.write(f"Threshold: {best_sharpe['Threshold']:,}")
                        st.write(f"Sharpe Ratio: {best_sharpe['Sharpe']:.2f}")
                        st.write(f"Max Drawdown: {best_sharpe['Max DD %']}%")
                        st.write(f"ROI: {best_sharpe['ROI %']}%")
                        st.write(f"Final Equity: ${best_sharpe['Final Equity']:,.0f}")
                    
                    # Display table
                    st.subheader("📋 Complete Results")
                    
                    # Format for display
                    display_df = results_df.copy()
                    display_df['Final Equity'] = display_df['Final Equity'].apply(lambda x: f"${x:,.0f}")
                    display_df['ROI %'] = display_df['ROI %'].apply(lambda x: f"{x:.1f}%")
                    display_df['Win Rate %'] = display_df['Win Rate %'].apply(lambda x: f"{x:.1f}%")
                    display_df['Max DD %'] = display_df['Max DD %'].apply(lambda x: f"{x:.1f}%")
                    display_df['Total Pips'] = display_df['Total Pips'].apply(lambda x: f"{x:,.0f}")
                    
                    # Sort by Profit Factor
                    display_df = display_df.sort_values('Profit Factor', ascending=False)
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Visualizations
                    st.subheader("📊 Visual Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig1 = px.bar(results_df, x='Threshold', y='Profit Factor',
                                     title='Profit Factor by Threshold',
                                     color='Profit Factor',
                                     color_continuous_scale='RdYlGn')
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    with col2:
                        fig2 = px.scatter(results_df, x='Max DD %', y='Profit Factor',
                                         size='Trades', color='Threshold',
                                         title='Risk-Reward Trade-off',
                                         hover_data=['Win Rate %', 'Sharpe'])
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    # Trade frequency analysis
                    fig3 = px.line(results_df, x='Threshold', y='Trades',
                                  title='Number of Trades by Threshold')
                    st.plotly_chart(fig3, use_container_width=True)

# ============================================
# TAB 4: Optimization (FIXED VERSION)
# ============================================
with tab4:
    st.header("⚡ Strategy Optimization")
    
    if st.session_state.cot_data is None:
        st.warning("Please load COT data first.")
    else:
        df = st.session_state.cot_data
        
        st.info("""
        **Your Results Show:**
        - **Best threshold is -30,000** (not the expected -50,000)
        - **High drawdowns** indicate need for risk management
        - **Profit factor > 1.2** suggests edge exists
        """)
        
        # Analysis of commercial positioning - FIXED VERSION
        st.subheader("📊 Commercial Positioning Analysis")
        
        # FIXED: Correct number of bins and labels
        bins = [-200000, -60000, -40000, -30000, -20000, -10000, 0]
        labels = [
            'Extreme Short (<-60k)', 
            'Very Short (-60k to -40k)', 
            'Short (-40k to -30k)', 
            'Moderate Short (-30k to -20k)', 
            'Mild Short (-20k to -10k)', 
            'Very Mild Short (-10k to 0)'
        ]
        
        # Check if all data fits in bins
        if df['commercial_net'].min() >= bins[0] and df['commercial_net'].max() <= bins[-1]:
            df['position_category'] = pd.cut(df['commercial_net'], bins=bins, labels=labels)
            
            category_counts = df['position_category'].value_counts().sort_index()
            category_pct = (category_counts / len(df) * 100).round(1)
            
            # Display frequency table
            freq_df = pd.DataFrame({
                'Position Category': category_counts.index,
                'Weeks': category_counts.values,
                'Percentage': category_pct.values
            })
            
            st.dataframe(freq_df, use_container_width=True)
            
            # Visualize
            fig = px.bar(freq_df, x='Percentage', y='Position Category', 
                         orientation='h', title='How Often Each Position Occurs')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Data outside bin range. Using simplified categorization.")
            
            # Simplified approach
            def categorize_position(net):
                if net < -60000:
                    return "Extreme Short (<-60k)"
                elif net < -40000:
                    return "Very Short (-60k to -40k)"
                elif net < -30000:
                    return "Short (-40k to -30k)"
                elif net < -20000:
                    return "Moderate Short (-30k to -20k)"
                elif net < -10000:
                    return "Mild Short (-20k to -10k)"
                else:
                    return "Very Mild Short (-10k to 0)"
            
            df['position_category'] = df['commercial_net'].apply(categorize_position)
            category_counts = df['position_category'].value_counts()
            category_pct = (category_counts / len(df) * 100).round(1)
            
            freq_df = pd.DataFrame({
                'Position Category': category_counts.index,
                'Weeks': category_counts.values,
                'Percentage': category_pct.values
            })
            
            st.dataframe(freq_df, use_container_width=True)
        
        # Risk Management Suggestions
        st.subheader("🛡️ Risk Management Recommendations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.warning("**⚠️ Current Issues:**")
            st.write("• 60%+ drawdown is extremely high")
            st.write("• Position sizing too aggressive")
            st.write("• No stop-loss in current strategy")
            st.write("• Weekly trading may be too frequent")
        
        with col2:
            st.success("**✅ Recommended Fixes:**")
            st.write("• Reduce risk to 0.5% per trade")
            st.write("• Add 100-pip stop loss")
            st.write("• Consider monthly instead of weekly trades")
            st.write("• Combine with other indicators")
        
        # Performance summary
        st.subheader("📈 Your Strategy Performance Summary")
        
        if 'current_stats' in st.session_state:
            stats = st.session_state.current_stats
            threshold = st.session_state.current_threshold
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Strategy Performance", 
                         f"{stats['roi_pct']}% ROI",
                         f"{stats['profit_factor']:.2f} PF")
            
            with col2:
                st.metric("Risk Metrics",
                         f"{stats['max_drawdown_pct']}% Max DD",
                         f"{stats['sharpe_ratio']:.2f} Sharpe")
            
            with col3:
                st.metric("Trade Statistics",
                         f"{stats['total_trades']} Trades",
                         f"{stats['win_rate']}% Win Rate")
            
            # Strategy assessment
            st.subheader("📋 Strategy Assessment")
            
            assessment = []
            
            # Profit Factor assessment
            if stats['profit_factor'] > 1.5:
                assessment.append(("✅ Profit Factor", "Excellent (>1.5)"))
            elif stats['profit_factor'] > 1.2:
                assessment.append(("✅ Profit Factor", "Good (1.2-1.5)"))
            else:
                assessment.append(("⚠️ Profit Factor", "Needs improvement (<1.2)"))
            
            # Drawdown assessment
            if stats['max_drawdown_pct'] > -20:
                assessment.append(("✅ Max Drawdown", "Good (<20%)"))
            elif stats['max_drawdown_pct'] > -40:
                assessment.append(("⚠️ Max Drawdown", "Acceptable (20-40%)"))
            else:
                assessment.append(("❌ Max Drawdown", "Risky (>40%) - NEEDS FIX"))
            
            # Win Rate assessment
            if stats['win_rate'] > 55:
                assessment.append(("✅ Win Rate", "Excellent (>55%)"))
            elif stats['win_rate'] > 50:
                assessment.append(("✅ Win Rate", "Good (50-55%)"))
            else:
                assessment.append(("⚠️ Win Rate", "Acceptable (<50%)"))
            
            # Sharpe Ratio assessment
            if stats['sharpe_ratio'] > 1.0:
                assessment.append(("✅ Sharpe Ratio", "Excellent (>1.0)"))
            elif stats['sharpe_ratio'] > 0.5:
                assessment.append(("✅ Sharpe Ratio", "Good (0.5-1.0)"))
            else:
                assessment.append(("⚠️ Sharpe Ratio", "Needs improvement (<0.5)"))
            
            # Display assessment
            for label, value in assessment:
                st.write(f"{label}: {value}")
            
            # Overall recommendation
            st.subheader("🎯 Final Recommendation")
            
            if stats['profit_factor'] > 1.2 and stats['max_drawdown_pct'] > -40:
                st.success("""
                **✅ STRATEGY IS PROMISING!**
                
                **Next Steps:**
                1. Implement risk management (0.5% risk, 100-pip stops)
                2. Paper trade for 3 months
                3. Consider combining with trend filter
                """)
            elif stats['profit_factor'] > 1.0:
                st.warning("""
                **⚠️ STRATEGY NEEDS IMPROVEMENT**
                
                **Issues to fix:**
                1. High drawdown is dangerous
                2. Reduce position size significantly
                3. Add stop-losses
                4. Consider different entry timing
                """)
            else:
                st.error("""
                **❌ STRATEGY NOT VIABLE**
                
                **Consider:**
                1. Different threshold values
                2. Alternative entry signals
                3. Different currency pair
                4. Longer holding periods
                """)

# Footer
st.divider()
st.caption("""
**COT Strategy Analyzer v2.1** | Data: 2020-2025 | 
**Key Finding:** Optimal threshold = -30,000 (Commercial Net) | 
**Warning:** High drawdown requires risk management
""")
