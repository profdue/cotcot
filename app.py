import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from cot_analyzer import COTAnalyzer
from trade_calculator import TradeCalculator
import config

# Page configuration
st.set_page_config(
    page_title="COT Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'cot_data' not in st.session_state:
    st.session_state.cot_data = None
if 'latest_signal' not in st.session_state:
    st.session_state.latest_signal = None

# App title
st.title("📊 COT-Based Trading Dashboard")
st.markdown("**Transform CFTC COT data into actionable USD/ZAR trades**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Trading Parameters")
    
    # Account settings
    account_balance = st.number_input(
        "Account Balance ($)",
        min_value=50.0,
        max_value=10000.0,
        value=float(config.INITIAL_CAPITAL),
        step=50.0
    )
    
    risk_percent = st.slider(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=2.0,
        value=float(config.RISK_PERCENT),
        step=0.1
    )
    
    st.divider()
    st.header("📈 Market Input")
    
    # Current price input
    current_price = st.number_input(
        f"Current {config.PRIMARY_PAIR} Price",
        min_value=10.0,
        max_value=30.0,
        value=18.5030,
        step=0.0001,
        format="%.4f"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        recent_low = st.number_input(
            "Recent Low (Support)",
            min_value=10.0,
            max_value=30.0,
            value=18.4500,
            step=0.0010,
            format="%.4f"
        )
    
    with col2:
        recent_high = st.number_input(
            "Recent High (Resistance)",
            min_value=10.0,
            max_value=30.0,
            value=18.6500,
            step=0.0010,
            format="%.4f"
        )
    
    st.divider()
    
    # Generate trade button
    generate_trade = st.button(
        "🎯 GENERATE TRADE PLAN",
        type="primary",
        use_container_width=True
    )

# Main content
tab1, tab2, tab3 = st.tabs(["📊 COT Dashboard", "🎯 Trade Plan", "📈 Historical Analysis"])

with tab1:
    st.header("Latest COT Signal")
    
    # Load data
    if st.button("Load COT Data"):
        try:
            # Get list of CSV files in data folder
            data_files = [
                "data/2020_COT.csv",
                "data/2021_COT.csv", 
                "data/2022_COT.csv",
                "data/2023_COT.csv",
                "data/2024_COT.csv"
            ]
            
            analyzer = COTAnalyzer(data_files)
            st.session_state.cot_data = analyzer
            st.session_state.latest_signal = analyzer.get_latest_signal()
            
            st.success("✅ COT data loaded successfully!")
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    # Display signal if available
    if st.session_state.latest_signal:
        signal = st.session_state.latest_signal
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Report Date",
                signal['report_date'].strftime("%b %d, %Y") if hasattr(signal['report_date'], 'strftime') else "N/A"
            )
        
        with col2:
            st.metric(
                "Commercial Net Position",
                f"{signal['net_commercial']:,}",
                delta="Short" if signal['net_commercial'] < 0 else "Long"
            )
        
        with col3:
            # Signal strength indicator
            strength_color = "red" if signal['signal_strength'] == "STRONG" else "gray"
            st.markdown(f"**Signal Strength:** :{strength_color}[{signal['signal_strength']}]")
        
        # Main signal box
        st.info(f"""
        ### 🎯 {signal['gold_signal']} GOLD
        **Translation:** {signal['usdzar_bias']}
        
        **Commercial Positions:**
        - Long: {signal['commercial_long']:,} ({signal['commercial_long_pct']}%)
        - Short: {signal['commercial_short']:,} ({signal['commercial_short_pct']}%)
        - Net: {signal['net_commercial']:,}
        """)
    
    else:
        st.warning("Click 'Load COT Data' to analyze the latest COT report")

with tab2:
    st.header("Trade Plan Generator")
    
    if generate_trade and st.session_state.latest_signal:
        # Initialize calculator
        calculator = TradeCalculator(account_balance, risk_percent)
        
        # Generate trade plan
        trade_plan = calculator.generate_trade_plan(
            st.session_state.latest_signal,
            current_price,
            recent_high,
            recent_low
        )
        
        if 'error' not in trade_plan:
            # Display trade plan
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Trade Details")
                
                direction_color = "green" if trade_plan['direction'] == "BUY" else "red"
                st.markdown(f"**Direction:** :{direction_color}[**{trade_plan['direction']}**]")
                st.markdown(f"**COT Signal:** {trade_plan['cot_signal']}")
                st.markdown(f"**Signal Strength:** {trade_plan['signal_strength']}")
                
                st.divider()
                
                st.subheader("🎯 Entry & Exit")
                st.metric("Entry Zone", trade_plan['entry_zone'])
                st.metric("Stop Loss", trade_plan['stop_loss'])
                st.metric("Take Profit", trade_plan['take_profit'])
            
            with col2:
                st.subheader("💰 Risk Management")
                
                st.metric("Risk/Reward", f"{trade_plan['risk_reward_ratio']}:1")
                st.metric("Risk (Pips)", trade_plan['risk_pips'])
                st.metric("Reward (Pips)", trade_plan['reward_pips'])
                
                st.divider()
                
                st.subheader("📝 Position Size")
                st.metric("Lot Size", trade_plan['position_size'])
                st.metric("Risk Amount", f"${trade_plan['risk_amount']}")
                st.metric("Account Balance", f"${account_balance}")
            
            # Trade setup explanation
            st.divider()
            st.subheader("📋 Trade Setup Checklist")
            
            checklist = """
            1. ✅ **COT Signal Confirmed:** {signal}
            2. ⏳ **Wait for Price Action:** Look for confirmation candle at {entry_zone}
            3. 🎯 **Entry:** Place {direction} order at {entry_zone}
            4. 🛑 **Stop Loss:** Set at {stop_loss}
            5. ✅ **Take Profit:** Set at {take_profit}
            6. 📊 **Risk/Reward:** {risk_pips} pips risk / {reward_pips} pips reward ({risk_reward_ratio}:1)
            7. 💰 **Position Size:** {position_size} lots (${risk_amount} risk)
            """.format(
                signal=trade_plan['cot_signal'],
                direction=trade_plan['direction'],
                entry_zone=trade_plan['entry_zone'],
                stop_loss=trade_plan['stop_loss'],
                take_profit=trade_plan['take_profit'],
                risk_pips=trade_plan['risk_pips'],
                reward_pips=trade_plan['reward_pips'],
                risk_reward_ratio=trade_plan['risk_reward_ratio'],
                position_size=trade_plan['position_size'],
                risk_amount=trade_plan['risk_amount']
            )
            
            st.info(checklist)
            
        else:
            st.error(trade_plan['error'])
    
    elif generate_trade and not st.session_state.latest_signal:
        st.warning("Please load COT data first!")
    else:
        st.info("Configure your parameters in the sidebar and click 'GENERATE TRADE PLAN'")

with tab3:
    st.header("Historical COT Analysis")
    
    if st.session_state.cot_data:
        analyzer = st.session_state.cot_data
        historical = analyzer.get_historical_signals(50)
        
        if historical:
            # Create dataframe for visualization
            df_hist = pd.DataFrame(historical)
            
            # Plot
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_hist['date'],
                y=df_hist['net_commercial'],
                mode='lines+markers',
                name='Commercial Net Position',
                line=dict(color='blue', width=2)
            ))
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            # Add threshold lines
            fig.add_hline(y=-50000, line_dash="dot", line_color="red", 
                         annotation_text="Extreme Short")
            fig.add_hline(y=50000, line_dash="dot", line_color="green",
                         annotation_text="Extreme Long")
            
            fig.update_layout(
                title="Commercial Net Position Over Time",
                xaxis_title="Date",
                yaxis_title="Net Position",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            st.subheader("Signal Statistics")
            signals = df_hist['signal'].value_counts()
            st.dataframe(signals)
            
    else:
        st.info("Load COT data to see historical analysis")

# Footer
st.divider()
st.caption("""
**Disclaimer:** This tool provides signals based on COT data. Always conduct your own analysis. 
Past performance is not indicative of future results. Trading involves risk of loss.
""")
