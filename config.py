"""
Configuration file for COT Trading App
"""

# Trading Parameters
INITIAL_CAPITAL = 150
RISK_PERCENT = 0.5  # 0.5% per trade
MAX_LOT_SIZE = 0.01  # Fixed until $300

# COT Signal Thresholds
COMMERCIAL_EXTREME_SHORT = -50000  # Net position threshold
COMMERCIAL_EXTREME_LONG = 50000    # Net position threshold

# Trading Instruments
PRIMARY_PAIR = "USD/ZAR"
SECONDARY_PAIR = "XAU/USD"  # Gold CFD
PIP_MULTIPLIER = 10000  # For USD/ZAR (4 decimal places)

# Risk Management
MIN_RISK_REWARD = 2.0  # Minimum 2:1 R:R
MAX_STOPLOSS_PIPS = 20

# App Settings
TIMEZONE = "Africa/Lagos"  # Change to your timezone
