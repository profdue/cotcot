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
    from price_action_checker import PriceActionChecker
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    # Create dummy classes for testing
    class COTAnalyzer:
        def __init__(self, data_paths): pass
        def get_latest_signal(self): 
            return {'error': 'Module not loaded', 'gold_signal': 'NEUTRAL', 'usdzar_bias': 'NEUTRAL'}
    
    class TradeCalculator:
        def __init__(self, account_balance=150, risk_percent=0.5): pass
        def generate_trade_plan(self, *args, **kwargs):
            return {'error': 'Module not loaded'}
    
    class PriceActionChecker:
        def __init__(self): pass
        def check_2_candle_rule(self, *args, **kwargs):
            return {'valid': False, 'reason': 'Module not loaded'}

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
        value=150.0,
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
    
    # Current price input
    current_price = st.number_input(
        "Current USD/ZAR Price",
        min_value=10.0,
        max_value=30.0,
        value=17.0537,
        step=0.0001,
        format="%.4f"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        recent_low = st.number_input(
            "Recent Low (Support)",
            min_value=10.0,
            max_value=30.0,
            value=17.0433,
            step=0.0010,
            format="%.4f"
        )
    
    with col2:
        recent_high = st.number_input(
            "Recent High (Resistance)",
            min_value=10.0,
            max_value=30.0,
            value=17.0590,
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

# Main content - TABS
tab1, tab2, tab3, tab4 = st.tabs(["📊 COT Dashboard", "🎯 Trade Plan", "✅ Price Action", "📈 Historical"])

# TAB 1: COT Dashboard
with tab1:
    st.header("Latest COT Signal")
    
    # Load data button
    if st.button("📂 Load COT Data"):
        try:
            # Get list of CSV files in data folder
            data_files = []
            for year in [2020, 2021, 2022, 2023, 2024]:
                file_path = f"data/{year}_COT.csv"
                if os.path.exists(file_path):
                    data_files.append(file_path)
            
            if data_files:
                analyzer = COTAnalyzer(data_files)
                st.session_state.cot_data = analyzer
                st.session_state.latest_signal = analyzer.get_latest_signal()
                st.success(f"✅ Loaded {len(data_files)} COT files successfully!")
            else:
                # Create sample data for testing
                st.session_state.latest_signal = {
                    'report_date': 'Dec 31, 2024',
                    'market': 'GOLD - COMMODITY EXCHANGE INC.',
                    'open_interest': 458691,
                    'commercial_long': 9983,
                    'commercial_short': 83344,
                    'net_commercial': -73361,
                    'commercial_long_pct': 2.18,
                    'commercial_short_pct': 18.17,
                    'gold_signal': 'BEARISH GOLD',
                    'usdzar_bias': 'BULLISH USD/ZAR',
                    'signal_strength': 'STRONG'
                }
                st.info("📝 Using sample data (no CSV files found in data/ folder)")
                
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    # Display signal if available
    if st.session_state.latest_signal and 'error' not in st.session_state.latest_signal:
        signal = st.session_state.latest_signal
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Report Date",
                signal.get('report_date', 'N/A')
            )
        
        with col2:
            net_pos = signal.get('net_commercial', 0)
            st.metric(
                "Commercial Net Position",
                f"{net_pos:,}",
                delta="Short" if net_pos < 0 else "Long"
            )
        
        with col3:
            strength = signal.get('signal_strength', 'UNKNOWN')
            strength_color = "red" if strength == "STRONG" else "orange" if strength == "MODERATE" else "gray"
            st.markdown(f"**Signal Strength:** :{strength_color}[{strength}]")
        
        # Main signal box
        st.info(f"""
        ### 🎯 {signal.get('gold_signal', 'NEUTRAL')} GOLD
        **Translation:** {signal.get('usdzar_bias', 'NEUTRAL')}
        
        **Commercial Positions:**
        - Long: {signal.get('commercial_long', 0):,} ({signal.get('commercial_long_pct', 0)}%)
        - Short: {signal.get('commercial_short', 0):,} ({signal.get('commercial_short_pct', 0)}%)
        - Net: {signal.get('net_commercial', 0):,}
        
        **Open Interest:** {signal.get('open_interest', 0):,} contracts
        """)
    
    else:
        st.warning("Click 'Load COT Data' to analyze the latest COT report")

# TAB 2: Trade Plan
with tab2:
    st.header("Trade Plan Generator")
    
    if generate_trade and st.session_state.latest_signal and 'error' not in st.session_state.latest_signal:
        # Initialize calculator
        calculator = TradeCalculator(account_balance, risk_percent)
        
        # Generate trade plan
        trade_plan = calculator.generate_trade_plan(
            st.session_state.latest_signal,
            current_price,
            recent_high,
            recent_low
        )
        
        st.session_state.trade_plan = trade_plan
        
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
                st.metric("Entry Zone", f"{trade_plan['entry_zone']:.4f}")
                st.metric("Stop Loss", f"{trade_plan['stop_loss']:.4f}")
                st.metric("Take Profit", f"{trade_plan['take_profit']:.4f}")
            
            with col2:
                st.subheader("💰 Risk Management")
                
                st.metric("Risk/Reward", f"{trade_plan['risk_reward_ratio']:.1f}:1")
                st.metric("Risk (Pips)", trade_plan['risk_pips'])
                st.metric("Reward (Pips)", trade_plan['reward_pips'])
                
                st.divider()
                
                st.subheader("📝 Position Size")
                st.metric("Lot Size", trade_plan['position_size'])
                st.metric("Risk Amount", f"${trade_plan['risk_amount']:.2f}")
                st.metric("Account Balance", f"${account_balance:.2f}")
            
            # Trade setup explanation
            st.divider()
            st.subheader("📋 Trade Setup Checklist")
            
            checklist = f"""
            1. ✅ **COT Signal Confirmed:** {trade_plan['cot_signal']}
            2. ⏳ **Wait for Price Action:** Look for confirmation candle at {trade_plan['entry_zone']:.4f}
            3. 🎯 **Entry:** Place {trade_plan['direction']} order at {trade_plan['entry_zone']:.4f}
            4. 🛑 **Stop Loss:** Set at {trade_plan['stop_loss']:.4f}
            5. ✅ **Take Profit:** Set at {trade_plan['take_profit']:.4f}
            6. 📊 **Risk/Reward:** {trade_plan['risk_pips']} pips risk / {trade_plan['reward_pips']} pips reward ({trade_plan['risk_reward_ratio']:.1f}:1)
            7. 💰 **Position Size:** {trade_plan['position_size']:.4f} lots (${trade_plan['risk_amount']:.2f} risk)
            """
            
            st.info(checklist)
            
            # Price Action Instructions
            st.divider()
            st.subheader("✅ Price Action Execution")
            
            if trade_plan['direction'] == "BUY":
                pa_instructions = f"""
                **Execution Rules for BUY:**
                
                1. **WAIT FOR:** Price to reach {trade_plan['entry_zone']:.4f}
                2. **LOOK FOR:** RED candle forming at support
                3. **CONFIRM WITH:** NEXT candle is GREEN and closes ABOVE red candle's high
                4. **ACTION:** Enter AFTER green candle closes
                5. **WARNING:** DO NOT enter during red candle
                
                Go to **✅ Price Action** tab to check your candles.
                """
            else:
                pa_instructions = f"""
                **Execution Rules for SELL:**
                
                1. **WAIT FOR:** Price to reach {trade_plan['entry_zone']:.4f}
                2. **LOOK FOR:** GREEN candle forming at resistance
                3. **CONFIRM WITH:** NEXT candle is RED and closes BELOW green candle's low
                4. **ACTION:** Enter AFTER red candle closes
                5. **WARNING:** DO NOT enter during green candle
                
                Go to **✅ Price Action** tab to check your candles.
                """
            
            st.success(pa_instructions)
            
        else:
            st.error(trade_plan['error'])
    
    elif generate_trade and not st.session_state.latest_signal:
        st.warning("Please load COT data first!")
    elif st.session_state.trade_plan and 'error' not in st.session_state.trade_plan:
        # Display existing trade plan
        trade_plan = st.session_state.trade_plan
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Active Trade Plan")
            st.metric("Direction", trade_plan['direction'])
            st.metric("Entry", f"{trade_plan['entry_zone']:.4f}")
            st.metric("Stop Loss", f"{trade_plan['stop_loss']:.4f}")
        
        with col2:
            st.subheader("💰 Risk Management")
            st.metric("Risk/Reward", f"{trade_plan['risk_reward_ratio']:.1f}:1")
            st.metric("Risk Amount", f"${trade_plan['risk_amount']:.2f}")
            st.metric("Position Size", trade_plan['position_size'])
        
        st.info("ℹ️ This is your current trade plan. Update parameters in sidebar and click 'GENERATE TRADE PLAN' to create a new one.")
    else:
        st.info("Configure your parameters in the sidebar and click 'GENERATE TRADE PLAN'")

# TAB 3: Price Action
with tab3:
    st.header("✅ Price Action Confirmation")
    st.markdown("**Use the 2-Candle Rule for entries**")
    
    # Initialize checker
    checker = PriceActionChecker()
    
    # Get current trade direction if available
    default_direction = "BUY"
    if st.session_state.trade_plan and 'error' not in st.session_state.trade_plan:
        default_direction = st.session_state.trade_plan['direction']
    
    # Direction selector
    direction = st.radio(
        "Trade Direction:",
        ["BUY", "SELL"],
        index=0 if default_direction == "BUY" else 1,
        horizontal=True
    )
    
    st.subheader(f"2-Candle Rule for {direction}")
    
    # Show visual example
    with st.expander("📸 Click to see pattern example", expanded=True):
        if direction == "BUY":
            st.markdown("""
            **BUY Pattern (2-Candle Rule):**
            
            ```
            Candle 1: 🔴 RED (Bearish)
              Open:  17.0480
              High:  17.0485
              Low:   17.0460  
              Close: 17.0470  ✗
            
            Candle 2: 🟢 GREEN (Bullish)  
              Open:  17.0470
              High:  17.0490  ✓
              Low:   17.0465
              Close: 17.0485  ✓
            
            ✅ RULE: GREEN closes ABOVE red high (17.0485 > 17.0485)
            ```
            """)
        else:
            st.markdown("""
            **SELL Pattern (2-Candle Rule):**
            
            ```
            Candle 1: 🟢 GREEN (Bullish)
              Open:  17.0580
              High:  17.0590
              Low:   17.0560  
              Close: 17.0585  ✗
            
            Candle 2: 🔴 RED (Bearish)  
              Open:  17.0585
              High:  17.0588
              Low:   17.0550  ✓
              Close: 17.0555  ✓
            
            ✅ RULE: RED closes BELOW green low (17.0555 < 17.0560)
            ```
            """)
    
    # Candle 1 Input
    st.markdown("---")
    st.subheader("📊 Candle 1 (First)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        c1_open = st.number_input("Open", value=17.0480, format="%.4f", key="c1o")
    with col2:
        c1_high = st.number_input("High", value=17.0485, format="%.4f", key="c1h")
    with col3:
        c1_low = st.number_input("Low", value=17.0460, format="%.4f", key="c1l")
    with col4:
        c1_close = st.number_input("Close", value=17.0470, format="%.4f", key="c1c")
    
    # Visual indicator for candle 1
    if c1_close > c1_open:
        candle1_color = "🟢 GREEN"
        candle1_status = "(Bullish - Close > Open)"
    elif c1_close < c1_open:
        candle1_color = "🔴 RED"
        candle1_status = "(Bearish - Close < Open)"
    else:
        candle1_color = "⚪ DOJI"
        candle1_status = "(Neutral - Close = Open)"
    
    st.markdown(f"**Candle 1:** {candle1_color} {candle1_status}")
    
    # Candle 2 Input
    st.markdown("---")
    st.subheader("📊 Candle 2 (Second - Confirmation)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        c2_open = st.number_input("Open", value=17.0470, format="%.4f", key="c2o")
    with col2:
        c2_high = st.number_input("High", value=17.0490, format="%.4f", key="c2h")
    with col3:
        c2_low = st.number_input("Low", value=17.0465, format="%.4f", key="c2l")
    with col4:
        c2_close = st.number_input("Close", value=17.0485, format="%.4f", key="c2c")
    
    # Visual indicator for candle 2
    if c2_close > c2_open:
        candle2_color = "🟢 GREEN"
        candle2_status = "(Bullish - Close > Open)"
    elif c2_close < c2_open:
        candle2_color = "🔴 RED"
        candle2_status = "(Bearish - Close < Open)"
    else:
        candle2_color = "⚪ DOJI"
        candle2_status = "(Neutral - Close = Open)"
    
    st.markdown(f"**Candle 2:** {candle2_color} {candle2_status}")
    
    # Check button
    if st.button("🔍 CHECK 2-CANDLE RULE", type="primary", use_container_width=True):
        # Prepare data
        candle_data = {
            'candle1': {
                'open': c1_open,
                'high': c1_high,
                'low': c1_low,
                'close': c1_close
            },
            'candle2': {
                'open': c2_open,
                'high': c2_high,
                'low': c2_low,
                'close': c2_close
            }
        }
        
        # Check the rule
        result = checker.check_2_candle_rule(direction, candle_data)
        
        # Display result
        if result.get('valid', False):
            st.success("🎉 **ENTRY CONFIRMED!**")
            
            # Show confirmation box
            st.markdown("---")
            st.subheader("✅ TRADE SIGNAL: GREEN LIGHT")
            
            st.info(f"""
            **Pattern Verified:** {result.get('reason', '2-Candle Rule Confirmed')}
            **Signal Strength:** {result.get('strength', 'STRONG')}
            **Rules Passed:** {result.get('rules_passed', 3)}/3
            
            ### 🎯 **YOU MAY ENTER THE TRADE**
            
            **Remember:**
            1. Set your stop loss immediately
            2. Set your take profit
            3. Don't move stops emotionally
            4. This is 0.01 lots only for $150 accounts
            """)
            
        else:
            st.error("❌ **ENTRY NOT CONFIRMED**")
            
            # Show what's wrong
            st.warning("""
            ### ⚠️ **DO NOT ENTER THE TRADE**
            
            The 2-candle rule is not satisfied.
            Wait for proper confirmation.
            
            **Common reasons to wait:**
            1. Candle colors are wrong sequence
            2. Second candle doesn't close beyond first candle
            3. Weak momentum
            4. Market is choppy/indecisive
            """)
            
            if 'details' in result:
                st.caption(f"**Details:** {result['details']}")
    
    # Quick guide
    st.markdown("---")
    st.subheader("📖 Quick Guide")
    
    if direction == "BUY":
        st.markdown("""
        **For BUY trades at support:**
        1. **WAIT** for price to reach your entry zone
        2. **LOOK** for a RED candle forming
        3. **WAIT** for NEXT candle to be GREEN
        4. **CONFIRM** GREEN closes ABOVE the RED candle's high
        5. **THEN** enter trade
        
        **Timeframe:** Use 5-minute or 15-minute charts
        **Patience:** Wait for the CLOSE of candle 2
        """)
    else:
        st.markdown("""
        **For SELL trades at resistance:**
        1. **WAIT** for price to reach your entry zone  
        2. **LOOK** for a GREEN candle forming
        3. **WAIT** for NEXT candle to be RED
        4. **CONFIRM** RED closes BELOW the GREEN candle's low
        5. **THEN** enter trade
        
        **Timeframe:** Use 5-minute or 15-minute charts
        **Patience:** Wait for the CLOSE of candle 2
        """)
    
    # Simple checklist
    st.markdown("---")
    st.subheader("✅ Mental Checklist")
    
    if direction == "BUY":
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Price is at support zone", value=False, key="check1")
            st.checkbox("First candle is RED", value=(c1_close < c1_open), key="check2")
        with col2:
            st.checkbox("Second candle is GREEN", value=(c2_close > c2_open), key="check3")
            st.checkbox("Green closes above red high", value=(c2_close > c1_high), key="check4")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Price is at resistance zone", value=False, key="check5")
            st.checkbox("First candle is GREEN", value=(c1_close > c1_open), key="check6")
        with col2:
            st.checkbox("Second candle is RED", value=(c2_close < c2_open), key="check7")
            st.checkbox("Red closes below green low", value=(c2_close < c1_low), key="check8")

# TAB 4: Historical Analysis
with tab4:
    st.header("Historical COT Analysis")
    
    if st.session_state.cot_data:
        analyzer = st.session_state.cot_data
        try:
            historical = analyzer.get_historical_signals(20)
            
            if historical:
                # Create dataframe
                df_hist = pd.DataFrame(historical)
                
                # Display table
                st.subheader("Recent COT Signals")
                st.dataframe(df_hist, use_container_width=True)
                
                # Simple statistics
                st.subheader("Signal Statistics")
                signal_counts = df_hist['signal'].value_counts()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    bullish_count = signal_counts.get('BULLISH', 0)
                    st.metric("Bullish Signals", bullish_count)
                
                with col2:
                    bearish_count = signal_counts.get('BEARISH', 0)
                    st.metric("Bearish Signals", bearish_count)
                
                with col3:
                    neutral_count = signal_counts.get('NEUTRAL', 0)
                    st.metric("Neutral Signals", neutral_count)
                
                # Simple text analysis
                if len(df_hist) >= 5:
                    recent_signals = df_hist.head(5)['signal'].tolist()
                    if all(s == 'BULLISH' for s in recent_signals):
                        st.info("📈 **Trend:** Strong bullish bias in recent weeks")
                    elif all(s == 'BEARISH' for s in recent_signals):
                        st.info("📉 **Trend:** Strong bearish bias in recent weeks")
                    else:
                        st.info("🔄 **Trend:** Mixed signals, market is choppy")
            else:
                st.info("No historical data available")
                
        except Exception as e:
            st.warning(f"Could not generate historical analysis: {e}")
            st.info("This feature requires proper COT data structure")
    else:
        st.info("Load COT data first to see historical analysis")

# Footer
st.divider()
st.caption("""
**Disclaimer:** This tool provides signals based on COT data and price action rules. Always conduct your own analysis. 
Past performance is not indicative of future results. Trading involves risk of loss. Start with 0.01 lots only.
""")
