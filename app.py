import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import custom modules
try:
    from cot_analyzer import COTAnalyzer
    from trade_calculator import TradeCalculator
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    # Create dummy classes
    class COTAnalyzer:
        def __init__(self, data_paths): pass
        def get_latest_signal(self): 
            return {'error': 'Module not loaded', 'gold_signal': 'NEUTRAL', 'usdzar_bias': 'NEUTRAL'}
    
    class TradeCalculator:
        def __init__(self, account_balance=150, risk_percent=0.5): pass
        def generate_trade_plan(self, *args, **kwargs):
            return {'error': 'Module not loaded'}

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
if 'trade_plan' not in st.session_state:
    st.session_state.trade_plan = None

# App title
st.title("📊 COT Trading Dashboard")
st.markdown("**Simple $150 Strategy: COT + Support/Resistance**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Trading Parameters")
    
    # Account settings
    account_balance = st.number_input(
        "Account Balance ($)",
        min_value=50.0,
        max_value=10000.0,
        value=100.0,
        step=50.0
    )
    
    risk_percent = st.slider(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=2.0,
        value=0.5,
        step=0.1
    )
    
    st.divider()
    st.header("📈 Market Input")
    
    # Simple: Just need today's range
    col1, col2 = st.columns(2)
    with col1:
        today_low = st.number_input(
            "Today's Low (Support)",
            min_value=10.0,
            max_value=30.0,
            value=17.0433,
            step=0.0010,
            format="%.4f",
            help="Lowest price today (from investing.com)"
        )
    
    with col2:
        today_high = st.number_input(
            "Today's High (Resistance)",
            min_value=10.0,
            max_value=30.0,
            value=17.0590,
            step=0.0010,
            format="%.4f",
            help="Highest price today (from investing.com)"
        )
    
    st.divider()
    
    # Generate trade button
    generate_trade = st.button(
        "🎯 GENERATE TRADE PLAN",
        type="primary",
        use_container_width=True
    )

# Main content - SIMPLIFIED TABS
tab1, tab2, tab3 = st.tabs(["📊 COT Signal", "🎯 Trade Plan", "✅ Simple Entry"])

# TAB 1: COT Signal
with tab1:
    st.header("COT Signal")
    
    # Load data button
    if st.button("📂 Load Latest COT Data"):
        try:
            # Auto-find all COT files
            import glob
            data_files = glob.glob("data/*COT*.csv")
            
            if data_files:
                analyzer = COTAnalyzer(data_files)
                st.session_state.cot_data = analyzer
                st.session_state.latest_signal = analyzer.get_latest_signal()
                st.success(f"✅ Loaded {len(data_files)} COT files")
            else:
                # Sample data
                st.session_state.latest_signal = {
                    'report_date': 'Nov 04, 2025',
                    'market': 'GOLD',
                    'commercial_long': 9805,
                    'commercial_short': 69256,
                    'net_commercial': -59451,
                    'gold_signal': 'BEARISH GOLD',
                    'usdzar_bias': 'BULLISH USD/ZAR',
                    'signal_strength': 'STRONG'
                }
                st.info("📝 Using sample COT data")
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Display signal
    if st.session_state.latest_signal and 'error' not in st.session_state.latest_signal:
        signal = st.session_state.latest_signal
        
        # Signal in simple terms
        st.subheader("🎯 Trading Signal")
        
        if "BULLISH USD/ZAR" in signal.get('usdzar_bias', ''):
            st.success(f"""
            ### 🟢 BUY USD/ZAR
            
            **Reason:** Commercials are SHORT {abs(signal.get('net_commercial', 0)):,} Gold contracts
            **When:** Price at SUPPORT ({today_low:.4f})
            **Strength:** {signal.get('signal_strength', 'UNKNOWN')}
            """)
        elif "BEARISH USD/ZAR" in signal.get('usdzar_bias', ''):
            st.error(f"""
            ### 🔴 SELL USD/ZAR
            
            **Reason:** Commercials are LONG {signal.get('net_commercial', 0):,} Gold contracts
            **When:** Price at RESISTANCE ({today_high:.4f})
            **Strength:** {signal.get('signal_strength', 'UNKNOWN')}
            """)
        else:
            st.warning("### ⚪ NO CLEAR SIGNAL")
        
        # Details (collapsed)
        with st.expander("📊 COT Details"):
            st.write(f"**Report Date:** {signal.get('report_date', 'N/A')}")
            st.write(f"**Commercial Long:** {signal.get('commercial_long', 0):,}")
            st.write(f"**Commercial Short:** {signal.get('commercial_short', 0):,}")
            st.write(f"**Net Position:** {signal.get('net_commercial', 0):,}")
    
    else:
        st.info("Click 'Load Latest COT Data' to get trading signal")

# TAB 2: Trade Plan
with tab2:
    st.header("Trade Plan")
    
    if generate_trade and st.session_state.latest_signal and 'error' not in st.session_state.latest_signal:
        # Get current price (approximate)
        current_price = (today_high + today_low) / 2
        
        # Generate simple trade plan
        signal = st.session_state.latest_signal
        usdzar_bias = signal.get('usdzar_bias', '').upper()
        
        if "BULLISH" in usdzar_bias:
            direction = "BUY"
            entry = today_low + 0.0010  # Just above support
            stop_loss = today_low - 0.0020  # 20 pips below
            take_profit = entry + 0.0040  # 40 pips above (2:1)
        elif "BEARISH" in usdzar_bias:
            direction = "SELL"
            entry = today_high - 0.0010  # Just below resistance
            stop_loss = today_high + 0.0020  # 20 pips above
            take_profit = entry - 0.0040  # 40 pips below (2:1)
        else:
            direction = "NONE"
            entry = stop_loss = take_profit = 0
        
        if direction != "NONE":
            # Risk calculation
            risk_amount = account_balance * (risk_percent / 100)
            position_size = 0.01  # Fixed for $100-$150 accounts
            
            st.session_state.trade_plan = {
                'direction': direction,
                'entry': round(entry, 4),
                'stop_loss': round(stop_loss, 4),
                'take_profit': round(take_profit, 4),
                'risk_amount': round(risk_amount, 2),
                'position_size': position_size
            }
            
            # Display plan
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Plan")
                color = "green" if direction == "BUY" else "red"
                st.markdown(f"**Direction:** :{color}[**{direction}**]")
                st.metric("Entry", f"{entry:.4f}")
                st.metric("Stop Loss", f"{stop_loss:.4f}")
                st.metric("Take Profit", f"{take_profit:.4f}")
            
            with col2:
                st.subheader("💰 Risk")
                st.metric("Risk/Reward", "2:1")
                st.metric("Risk Amount", f"${risk_amount:.2f}")
                st.metric("Position Size", f"{position_size} lots")
                st.metric("Account", f"${account_balance:.0f}")
            
            # Simple instructions
            st.divider()
            st.subheader("📋 Simple Rules")
            
            if direction == "BUY":
                st.info(f"""
                1. **WAIT** for price to reach **{entry:.4f}**
                2. **ENTER** BUY order
                3. **STOP** at {stop_loss:.4f}
                4. **TARGET** {take_profit:.4f}
                5. **WALK AWAY** for 2 hours
                
                ⚠️ **Only enter if price is near {entry:.4f}**
                """)
            else:
                st.info(f"""
                1. **WAIT** for price to reach **{entry:.4f}**
                2. **ENTER** SELL order
                3. **STOP** at {stop_loss:.4f}
                4. **TARGET** {take_profit:.4f}
                5. **WALK AWAY** for 2 hours
                
                ⚠️ **Only enter if price is near {entry:.4f}**
                """)
        else:
            st.warning("No clear signal from COT data")
    
    elif st.session_state.trade_plan:
        # Show existing plan
        tp = st.session_state.trade_plan
        
        st.subheader("📊 Active Trade Plan")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Direction", tp['direction'])
            st.metric("Entry", f"{tp['entry']:.4f}")
            st.metric("Stop Loss", f"{tp['stop_loss']:.4f}")
        
        with col2:
            st.metric("Take Profit", f"{tp['take_profit']:.4f}")
            st.metric("Risk Amount", f"${tp['risk_amount']:.2f}")
            st.metric("Position Size", tp['position_size'])
        
        st.info("Update parameters in sidebar and click 'GENERATE TRADE PLAN' for new plan")
    
    else:
        st.info("Configure parameters and click 'GENERATE TRADE PLAN'")

# TAB 3: Simple Entry (REPLACES Price Action)
with tab3:
    st.header("✅ Simple Entry Check")
    
    st.markdown("""
    ### 🎯 No Stress Entry System
    
    **Forget complex patterns. Just follow these simple rules:**
    
    1. **Get your entry level** from Trade Plan tab
    2. **Watch price approach** that level
    3. **Enter when price is CLOSE** (within 5 pips)
    4. **Set stop and target immediately**
    5. **Walk away**
    """)
    
    # Get current trade plan
    if st.session_state.trade_plan:
        tp = st.session_state.trade_plan
        
        st.subheader("📊 Your Current Plan")
        st.write(f"**Direction:** {tp['direction']}")
        st.write(f"**Entry Level:** {tp['entry']:.4f}")
        st.write(f"**Stop Loss:** {tp['stop_loss']:.4f}")
        st.write(f"**Take Profit:** {tp['take_profit']:.4f}")
        
        st.divider()
        
        # Simple check
        st.subheader("✅ Entry Check")
        
        current_near_entry = st.radio(
            "Is current price NEAR your entry level?",
            ["YES - Within 5 pips", "NO - Far away", "NOT SURE"]
        )
        
        price_trend = st.radio(
            "Is price moving TOWARD your entry?",
            ["YES - Getting closer", "NO - Moving away", "SIDEWAYS - Not moving"]
        )
        
        market_time = st.radio(
            "Current time?",
            ["LONDON/NY SESSION (Good)", "ASIAN SESSION (Avoid)", "WEEKEND (No Trade)"]
        )
        
        # Evaluate
        if st.button("🔍 CHECK IF READY TO ENTER"):
            score = 0
            if "YES" in current_near_entry: score += 1
            if "YES" in price_trend: score += 1
            if "LONDON/NY" in market_time: score += 1
            
            if score == 3:
                st.success("""
                🎉 **GREEN LIGHT - READY TO ENTER!**
                
                **Action:**
                1. Place 0.01 lot order
                2. Set stop at {tp['stop_loss']:.4f}
                3. Set target at {tp['take_profit']:.4f}
                4. Close platform for 2 hours
                """)
            elif score >= 2:
                st.warning("""
                🟡 **YELLOW LIGHT - BE CAREFUL**
                
                Conditions aren't perfect. Consider:
                - Waiting 30 minutes
                - Using smaller position (0.005 lots)
                - Setting tighter stop
                """)
            else:
                st.error("""
                🔴 **RED LIGHT - DO NOT ENTER**
                
                **Reasons:**
                - Wrong price level
                - Wrong market session
                - Price moving away
                
                **Action:** Wait or no trade today
                """)
    else:
        st.info("Generate a trade plan first in the Trade Plan tab")
    
    # Simple rules
    st.divider()
    st.subheader("📖 Golden Rules")
    
    st.markdown("""
    1. **Only 1 trade per day**
    2. **Only during London/NY overlap** (2PM-6PM Nigeria time)
    3. **Only 0.01 lots** until account > $300
    4. **Never move stop loss** once set
    5. **If unsure, NO TRADE**
    6. **Missing trades costs $0, bad trades cost money**
    """)

# Footer
st.divider()
st.caption("""
**For $100-$150 accounts:** Keep it simple. 1 trade/day, 0.01 lots, 2:1 risk/reward. 
Patience beats complexity. Trade only when ALL conditions align.
""")
