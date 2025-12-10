import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import custom modules
try:
    from cot_analyzer import COTAnalyzer
except ImportError:
    # Simple fallback
    class COTAnalyzer:
        def __init__(self, data_paths): pass
        def get_latest_signal(self): 
            return self._get_sample_signal()
        def _get_sample_signal(self):
            return {
                'report_date': 'Nov 04, 2025',
                'commercial_long': 9805,
                'commercial_short': 69256,
                'net_commercial': -59451,
                'gold_signal': 'BEARISH GOLD',
                'usdzar_bias': 'BULLISH USD/ZAR',
                'signal_strength': 'STRONG'
            }

# Page configuration
st.set_page_config(
    page_title="COT Limit Order Trader",
    page_icon="🎯",
    layout="wide"
)

# App title
st.title("🎯 COT Limit Order Trader")
st.markdown("**Set & Forget Trading for $150 Accounts**")

# Initialize session state
if 'latest_signal' not in st.session_state:
    st.session_state.latest_signal = None

# Main content - SINGLE DASHBOARD (No Tabs!)
st.header("1. 📊 Get COT Signal")

# Load COT button
if st.button("📈 Load Latest COT Report", type="primary"):
    try:
        import glob
        data_files = glob.glob("data/*COT*.csv")
        
        if data_files:
            analyzer = COTAnalyzer(data_files)
            st.session_state.latest_signal = analyzer.get_latest_signal()
            st.success(f"✅ COT Signal Loaded")
        else:
            st.session_state.latest_signal = COTAnalyzer()._get_sample_signal()
            st.info("📝 Using sample COT data")
            
    except Exception as e:
        st.error(f"Error: {e}")

# Display signal if available
if st.session_state.latest_signal:
    signal = st.session_state.latest_signal
    
    # Show clear signal
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("COT Report Date", signal.get('report_date', 'N/A'))
    
    with col2:
        net = signal.get('net_commercial', 0)
        st.metric("Commercial Net", f"{net:,}", delta="Short" if net < 0 else "Long")
    
    with col3:
        bias = signal.get('usdzar_bias', 'NEUTRAL')
        if "BULLISH" in bias:
            st.metric("USD/ZAR Signal", "🟢 BUY", delta="Strong" if signal.get('signal_strength') == 'STRONG' else "Moderate")
        elif "BEARISH" in bias:
            st.metric("USD/ZAR Signal", "🔴 SELL", delta="Strong" if signal.get('signal_strength') == 'STRONG' else "Moderate")
        else:
            st.metric("USD/ZAR Signal", "⚪ WAIT")
    
    # Simple explanation
    if "BULLISH" in signal.get('usdzar_bias', ''):
        st.info(f"**🎯 Trading Bias:** BUY USD/ZAR - Commercials are SHORT {abs(signal.get('net_commercial', 0)):,} Gold contracts")
    elif "BEARISH" in signal.get('usdzar_bias', ''):
        st.info(f"**🎯 Trading Bias:** SELL USD/ZAR - Commercials are LONG {signal.get('net_commercial', 0):,} Gold contracts")
    else:
        st.warning("**🎯 Trading Bias:** NEUTRAL - Wait for clearer signal")

st.divider()

# STEP 2: Market Levels
st.header("2. 📈 Enter Today's Market Levels")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Today's Range")
    today_low = st.number_input(
        "Today's Low (Support)",
        min_value=10.0,
        max_value=30.0,
        value=17.0433,
        step=0.0010,
        format="%.4f",
        help="From investing.com - Day's Range Low"
    )
    
    today_high = st.number_input(
        "Today's High (Resistance)", 
        min_value=10.0,
        max_value=30.0,
        value=17.0590,
        step=0.0010,
        format="%.4f",
        help="From investing.com - Day's Range High"
    )

with col2:
    st.subheader("Account Settings")
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

# STEP 3: Generate Limit Order
st.header("3. 🎯 Generate Limit Order")

if st.button("✨ GENERATE LIMIT ORDER", type="primary", use_container_width=True):
    if not st.session_state.latest_signal:
        st.error("Please load COT data first!")
    else:
        signal = st.session_state.latest_signal
        bias = signal.get('usdzar_bias', '').upper()
        
        # Calculate order details
        if "BULLISH" in bias:
            direction = "BUY"
            order_type = "BUY LIMIT"
            entry_price = round(today_low + 0.0010, 4)  # Just above support
            stop_loss = round(today_low - 0.0020, 4)    # 20 pips below
            take_profit = round(entry_price + 0.0040, 4)  # 40 pips above (2:1)
            explanation = f"Price needs to DROP to support at {today_low:.4f}"
            
        elif "BEARISH" in bias:
            direction = "SELL" 
            order_type = "SELL LIMIT"
            entry_price = round(today_high - 0.0010, 4)  # Just below resistance
            stop_loss = round(today_high + 0.0020, 4)     # 20 pips above
            take_profit = round(entry_price - 0.0040, 4)  # 40 pips below (2:1)
            explanation = f"Price needs to RISE to resistance at {today_high:.4f}"
            
        else:
            direction = "NONE"
            order_type = "NO ORDER"
            entry_price = stop_loss = take_profit = 0
            explanation = "No clear signal - wait"
        
        if direction != "NONE":
            # Risk calculation
            risk_amount = account_balance * (risk_percent / 100)
            position_size = 0.01  # Fixed for small accounts
            
            # Save to session
            st.session_state.order_details = {
                'direction': direction,
                'order_type': order_type,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': round(risk_amount, 2),
                'position_size': position_size,
                'explanation': explanation
            }
            
            # Display order
            st.success("✅ LIMIT ORDER GENERATED!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Order Details")
                st.metric("Order Type", order_type)
                st.metric("Entry Price", f"{entry_price:.4f}")
                st.metric("Stop Loss", f"{stop_loss:.4f}")
                st.metric("Take Profit", f"{take_profit:.4f}")
            
            with col2:
                st.subheader("💰 Risk Management")
                st.metric("Risk/Reward", "2:1")
                st.metric("Risk Amount", f"${risk_amount:.2f}")
                st.metric("Position Size", f"{position_size} lots")
                st.metric("Pips Risk", "20")
                st.metric("Pips Reward", "40")
            
            # Broker instructions
            st.divider()
            st.header("4. 📱 How to Set This Order")
            
            # Platform selector
            platform = st.selectbox(
                "Select Your Broker Platform:",
                ["Exness", "XM", "FBS", "OctaFX", "HotForex", "Other"]
            )
            
            # Platform-specific instructions
            if platform == "Exness":
                instructions = f"""
                1. **Open Exness app** → USD/ZAR chart
                2. **Tap "New Order"** (usually + icon)
                3. **Select "Pending Order"**
                4. **Choose "{order_type}"**
                5. **Set Price:** {entry_price:.4f}
                6. **Set Stop Loss:** {stop_loss:.4f}
                7. **Set Take Profit:** {take_profit:.4f}
                8. **Set Volume:** 0.01
                9. **Expiry:** Tomorrow 9AM
                10. **Tap "Place Order"**
                
                💡 **Pro Tip:** Set order, then close app. Check back in 6 hours.
                """
            elif platform == "XM":
                instructions = f"""
                1. **Open XM app** → USD/ZAR
                2. **Tap "Trade"** (bottom middle)
                3. **Tap "Pending Order"** (top right)
                4. **Select "{order_type}"**
                5. **Price:** {entry_price:.4f}
                6. **Stop Loss:** {stop_loss:.4f}
                7. **Take Profit:** {take_profit:.4f}
                8. **Lots:** 0.01
                9. **Expiry:** GTC (Good Till Cancelled)
                10. **Confirm Order**
                """
            else:
                instructions = f"""
                1. Open your {platform} trading platform
                2. Go to USD/ZAR chart
                3. Look for "Pending Orders" or "Limit Orders"
                4. Select **{order_type}**
                5. Set price to **{entry_price:.4f}**
                6. Set stop loss to **{stop_loss:.4f}**
                7. Set take profit to **{take_profit:.4f}**
                8. Set volume to **0.01 lots**
                9. Place order
                10. Close platform and check later
                """
            
            st.info(instructions)
            
            # Market context
            st.divider()
            st.header("5. 📊 Market Context")
            
            current_mid = (today_high + today_low) / 2
            st.write(f"**Current Market Situation:**")
            st.write(f"- Today's Range: {today_low:.4f} to {today_high:.4f}")
            st.write(f"- Your Entry: {entry_price:.4f}")
            st.write(f"- **{explanation}**")
            
            # Probability estimate
            st.divider()
            st.header("6. 🎲 Probability & Expectations")
            
            if direction == "BUY":
                st.write("""
                **What to Expect:**
                - ✅ **GOOD:** Price drops to support, order fills, hits target
                - ⚠️ **OK:** Price drops but not enough, order doesn't fill (no loss)
                - ❌ **BAD:** Price drops sharply, fills then hits stop loss (lose $0.50)
                
                **Probability:** 40-60% fill rate (depends on market volatility)
                **Best Time:** London/NY overlap (2PM-6PM Nigeria time)
                """)
            else:
                st.write("""
                **What to Expect:**
                - ✅ **GOOD:** Price rises to resistance, order fills, hits target
                - ⚠️ **OK:** Price rises but not enough, order doesn't fill (no loss)
                - ❌ **BAD:** Price spikes then reverses, hits stop loss (lose $0.50)
                
                **Probability:** 40-60% fill rate
                **Best Time:** London/NY overlap
                """)
            
            # Golden rules
            st.divider()
            st.header("7. ⭐ Golden Rules for $150 Accounts")
            
            st.markdown("""
            1. **ONLY 0.01 lots** until account > $300
            2. **ONLY 1 pending order at a time**
            3. **NEVER move stop loss** once set
            4. **ALWAYS set take profit** (greed loses accounts)
            5. **If order doesn't fill in 24 hours, CANCEL it**
            6. **Missing trades costs $0, bad trades cost money**
            7. **Patience beats rushing** - Wait for price to come to you
            8. **Weekends:** Cancel all pending orders Friday evening
            """)
            
        else:
            st.warning("No clear trading signal from COT data. Wait for next COT report.")

# Footer
st.divider()
st.caption("""
**Strategy:** COT-based limit orders | **Risk:** 0.5% per trade | **Lots:** 0.01 fixed | **Pairs:** USD/ZAR only
**Remember:** This is a SET & FORGET system. Place order, close app, live your life.
""")
