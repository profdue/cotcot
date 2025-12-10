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
    from trade_calculator import TradeCalculator
except ImportError:
    # Create dummy classes
    class COTAnalyzer:
        def __init__(self, data_paths): pass
        def get_latest_signal(self): 
            return {
                'report_date': 'Latest Report',
                'usdzar_bias': 'BULLISH USD/ZAR',
                'signal_strength': 'STRONG',
                'net_commercial': -59451
            }
    
    class TradeCalculator:
        def __init__(self, account_balance=150, risk_percent=0.5): 
            self.account_balance = account_balance
            self.risk_percent = risk_percent

# Page configuration
st.set_page_config(
    page_title="COT Limit Order Dashboard",
    page_icon="🎯",
    layout="wide"
)

# App title
st.title("🎯 COT Limit Order Dashboard")
st.markdown("**Set & Forget Trading for $150 Accounts**")

# Initialize session state
if 'trade_plan' not in st.session_state:
    st.session_state.trade_plan = None
if 'orders_set' not in st.session_state:
    st.session_state.orders_set = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Account Settings")
    
    account_balance = st.number_input(
        "Account Balance ($)",
        min_value=50.0,
        max_value=1000.0,
        value=100.0,
        step=50.0,
        help="Your trading account balance"
    )
    
    risk_percent = st.slider(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=2.0,
        value=0.5,
        step=0.1,
        help="Risk 0.5% = $0.50 risk on $100 account"
    )
    
    st.divider()
    st.header("📈 Market Levels")
    
    # Today's range
    col1, col2 = st.columns(2)
    with col1:
        support = st.number_input(
            "Support (Buy Zone)",
            min_value=10.0,
            max_value=30.0,
            value=17.0433,
            step=0.0010,
            format="%.4f",
            help="Today's low from investing.com"
        )
    
    with col2:
        resistance = st.number_input(
            "Resistance (Sell Zone)",
            min_value=10.0,
            max_value=30.0,
            value=17.0590,
            step=0.0010,
            format="%.4f",
            help="Today's high from investing.com"
        )
    
    current_price = (support + resistance) / 2
    
    st.divider()
    
    # Generate button
    generate = st.button(
        "🚀 GENERATE LIMIT ORDERS",
        type="primary",
        use_container_width=True
    )

# Main content
tab1, tab2, tab3 = st.tabs(["🎯 Order Setup", "📱 Broker Guide", "📊 COT Signal"])

# TAB 1: Order Setup
with tab1:
    st.header("🎯 Limit Order Setup")
    
    if generate:
        # Load COT signal
        try:
            data_files = []
            for year in [2020, 2021, 2022, 2023, 2024, 2025]:
                file_path = f"data/{year}_COT.csv"
                if os.path.exists(file_path):
                    data_files.append(file_path)
            
            if data_files:
                analyzer = COTAnalyzer(data_files)
                signal = analyzer.get_latest_signal()
            else:
                signal = analyzer.get_latest_signal()  # Use dummy
        except:
            signal = {'usdzar_bias': 'BULLISH USD/ZAR', 'signal_strength': 'STRONG'}
        
        # Generate orders based on signal
        bias = signal.get('usdzar_bias', '').upper()
        
        if "BULLISH" in bias:
            direction = "BUY"
            order_type = "BUY LIMIT"
            entry_price = support + 0.0010
            stop_loss = support - 0.0020
            take_profit = entry_price + 0.0040
            
            # Explanation
            reason = f"Commercials are SHORT {abs(signal.get('net_commercial', 59451)):,} Gold contracts"
            
        elif "BEARISH" in bias:
            direction = "SELL"
            order_type = "SELL LIMIT"
            entry_price = resistance - 0.0010
            stop_loss = resistance + 0.0020
            take_profit = entry_price - 0.0040
            
            reason = f"Commercials are LONG {signal.get('net_commercial', 0):,} Gold contracts"
        else:
            direction = "NEUTRAL"
            order_type = "NO TRADE"
            entry_price = stop_loss = take_profit = 0
            reason = "No clear COT signal"
        
        if direction != "NEUTRAL":
            # Calculate risk
            risk_pips = abs(entry_price - stop_loss) * 10000
            reward_pips = abs(take_profit - entry_price) * 10000
            risk_amount = account_balance * (risk_percent / 100)
            
            # Save plan
            st.session_state.trade_plan = {
                'direction': direction,
                'order_type': order_type,
                'entry': round(entry_price, 4),
                'stop_loss': round(stop_loss, 4),
                'take_profit': round(take_profit, 4),
                'risk_pips': int(risk_pips),
                'reward_pips': int(reward_pips),
                'risk_amount': round(risk_amount, 2),
                'position_size': 0.01,
                'reason': reason,
                'signal_strength': signal.get('signal_strength', 'STRONG'),
                'valid_until': (datetime.now() + timedelta(days=1)).strftime("%b %d, %Y 9:00 AM")
            }
    
    # Display order plan
    if st.session_state.trade_plan:
        tp = st.session_state.trade_plan
        
        st.success(f"### 🎯 {tp['direction']} SIGNAL DETECTED")
        st.write(f"**Reason:** {tp['reason']}")
        st.write(f"**Signal Strength:** {tp['signal_strength']}")
        
        # Order details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Order Type", tp['order_type'])
            st.metric("Entry Price", f"{tp['entry']:.4f}")
        
        with col2:
            st.metric("Stop Loss", f"{tp['stop_loss']:.4f}")
            st.metric("Take Profit", f"{tp['take_profit']:.4f}")
        
        with col3:
            st.metric("Risk/Reward", f"{tp['risk_pips']}/{tp['reward_pips']} pips")
            st.metric("Risk Amount", f"${tp['risk_amount']:.2f}")
        
        # Order ticket
        st.divider()
        st.subheader("📝 Order Ticket")
        
        order_ticket = f"""
        **{tp['order_type']} ORDER**
        Symbol: USD/ZAR
        Volume: {tp['position_size']} lots
        Price: {tp['entry']:.4f}
        Stop Loss: {tp['stop_loss']:.4f}
        Take Profit: {tp['take_profit']:.4f}
        Expiry: {tp['valid_until']}
        """
        
        st.code(order_ticket, language="text")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ MARK AS SET", type="primary", use_container_width=True):
                st.session_state.orders_set = True
                st.rerun()
        
        with col2:
            if st.button("🔄 NEW SIGNAL", use_container_width=True):
                st.session_state.trade_plan = None
                st.session_state.orders_set = False
                st.rerun()
        
        # Status
        if st.session_state.orders_set:
            st.balloons()
            st.success("""
            ✅ **ORDERS SET SUCCESSFULLY!**
            
            **Now go live your life:**
            1. Orders will execute automatically
            2. Check back tomorrow morning
            3. If filled, manage trade
            4. If not filled, check for new signal
            """)
    
    else:
        st.info("Click 'GENERATE LIMIT ORDERS' to get your trading orders")

# TAB 2: Broker Guide
with tab2:
    st.header("📱 How to Set Orders")
    
    if st.session_state.trade_plan:
        tp = st.session_state.trade_plan
        
        # Select broker
        broker = st.selectbox(
            "Select Your Broker",
            ["Exness", "XM", "FBS", "OctaFX", "HotForex"]
        )
        
        st.subheader(f"Step-by-Step for {broker}")
        
        if broker == "Exness":
            steps = """
            1. **Open Exness app** on your phone
            2. **Go to USD/ZAR** chart
            3. Tap **"Trade"** button
            4. Select **"Pending Order"**
            5. Choose **"{order_type}"**
            6. Set **Price: {entry:.4f}**
            7. Set **Stop Loss: {stop_loss:.4f}**
            8. Set **Take Profit: {take_profit:.4f}**
            9. Set **Volume: 0.01** lots
            10. Tap **"Place Order"**
            11. **CONFIRM** the order
            """.format(
                order_type=tp['order_type'],
                entry=tp['entry'],
                stop_loss=tp['stop_loss'],
                take_profit=tp['take_profit']
            )
        
        elif broker == "XM":
            steps = """
            1. **Open XM app**
            2. Go to **USD/ZAR**
            3. Tap **"+"** or **"New Order"**
            4. Select **"Pending Order"**
            5. Choose **"{order_type}"**
            6. Set **Entry: {entry:.4f}**
            7. Set **S/L: {stop_loss:.4f}**
            8. Set **T/P: {take_profit:.4f}**
            9. Set **Lots: 0.01**
            10. Tap **"Place Order"**
            """.format(
                order_type=tp['order_type'],
                entry=tp['entry'],
                stop_loss=tp['stop_loss'],
                take_profit=tp['take_profit']
            )
        
        else:
            steps = f"""
            1. Open your {broker} app
            2. Find USD/ZAR
            3. Create Pending Order
            4. Select {tp['order_type']}
            5. Price: {tp['entry']:.4f}
            6. Stop Loss: {tp['stop_loss']:.4f}
            7. Take Profit: {tp['take_profit']:.4f}
            8. Volume: 0.01 lots
            9. Place Order
            """
        
        st.info(steps)
        
        # Visual guide
        with st.expander("📸 Visual Guide (What to look for)"):
            st.image("https://via.placeholder.com/400x250/4CAF50/FFFFFF?text=BUY+LIMIT+Example", 
                    caption="Example: BUY LIMIT order setup")
            st.write("""
            **Key terms in your broker:**
            - **Pending Order**: Order that waits for price
            - **Buy Limit**: Buy BELOW current price
            - **Sell Limit**: Sell ABOVE current price  
            - **S/L**: Stop Loss
            - **T/P**: Take Profit
            - **Volume**: Lot size (use 0.01)
            """)
    
    else:
        st.info("Generate orders first in the Order Setup tab")

# TAB 3: COT Signal
with tab3:
    st.header("📊 COT Signal Analysis")
    
    # Simple signal display
    st.info("""
    ### How COT Signals Work:
    
    **Commercial Traders (Smart Money)** positions in Gold:
    - **SHORT Commercials** = BEARISH Gold = BULLISH USD/ZAR
    - **LONG Commercials** = BULLISH Gold = BEARISH USD/ZAR
    
    **Thresholds:**
    - > +50,000: STRONG BULLISH Gold
    - < -50,000: STRONG BEARISH Gold
    - Between: Moderate signal
    """)
    
    # Load and show current signal
    if st.button("🔄 Refresh COT Data"):
        try:
            data_files = []
            for year in [2020, 2021, 2022, 2023, 2024, 2025]:
                file_path = f"data/{year}_COT.csv"
                if os.path.exists(file_path):
                    data_files.append(file_path)
            
            if data_files:
                analyzer = COTAnalyzer(data_files)
                signal = analyzer.get_latest_signal()
                
                st.subheader("📈 Latest COT Report")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Report Date", signal.get('report_date', 'N/A'))
                    st.metric("Net Commercial", f"{signal.get('net_commercial', 0):,}")
                
                with col2:
                    bias = signal.get('usdzar_bias', 'NEUTRAL')
                    color = "green" if "BULLISH" in bias else "red" if "BEARISH" in bias else "gray"
                    st.markdown(f"**USD/ZAR Bias:** :{color}[{bias}]")
                    st.metric("Signal Strength", signal.get('signal_strength', 'UNKNOWN'))
                
                # Interpretation
                net = signal.get('net_commercial', 0)
                if net < -50000:
                    st.success("""
                    🟢 **STRONG BUY USD/ZAR SIGNAL**
                    
                    Commercials are heavily SHORT Gold.
                    Look for BUY LIMIT orders at support.
                    """)
                elif net > 50000:
                    st.error("""
                    🔴 **STRONG SELL USD/ZAR SIGNAL**
                    
                    Commercials are heavily LONG Gold.
                    Look for SELL LIMIT orders at resistance.
                    """)
                else:
                    st.warning("""
                    🟡 **MODERATE OR NO SIGNAL**
                    
                    Commercial position not extreme.
                    Consider waiting for clearer signal.
                    """)
            else:
                st.warning("No COT files found in data folder")
                
        except Exception as e:
            st.error(f"Error loading COT data: {e}")

# Footer
st.divider()
st.caption("""
**$150 Strategy Rules:**
1. Only 0.01 lots until $300
2. Only 1 pending order at a time
3. Orders valid for 24 hours max
4. Cancel unfilled orders next morning
5. Always use Stop Loss & Take Profit
""")
