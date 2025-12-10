"""
Simple 2-Candle Rule Price Action Checker
For $150 accounts - keeps it SIMPLE
"""

class PriceActionChecker:
    def __init__(self):
        self.rules = {
            'buy': {
                'name': '2-Candle Bullish Reversal',
                'description': 'Red candle followed by GREEN candle closing above red high',
                'conditions': [
                    'Price is at support zone',
                    'First candle: RED (closes lower than opens)',
                    'Second candle: GREEN (closes higher than opens)',
                    'Green candle closes ABOVE red candle high'
                ]
            },
            'sell': {
                'name': '2-Candle Bearish Reversal',
                'description': 'Green candle followed by RED candle closing below green low',
                'conditions': [
                    'Price is at resistance zone',
                    'First candle: GREEN (closes higher than opens)',
                    'Second candle: RED (closes lower than opens)',
                    'Red candle closes BELOW green candle low'
                ]
            }
        }
    
    def check_2_candle_rule(self, direction, candle_data):
        """
        Check if 2-candle rule is satisfied
        
        candle_data format:
        {
            'candle1': {'open': 17.0480, 'close': 17.0470, 'high': 17.0485, 'low': 17.0460},
            'candle2': {'open': 17.0470, 'close': 17.0485, 'high': 17.0490, 'low': 17.0465}
        }
        
        Returns:
        {
            'valid': True/False,
            'reason': 'Description',
            'strength': 'STRONG/MODERATE/WEAK',
            'rules_passed': int,
            'details': 'Additional info'
        }
        """
        if not candle_data or 'candle1' not in candle_data or 'candle2' not in candle_data:
            return {
                'valid': False,
                'reason': 'Incomplete candle data',
                'strength': 'INVALID',
                'rules_passed': 0
            }
        
        direction = direction.upper()
        
        if direction == 'BUY':
            return self._check_buy_rule(candle_data)
        elif direction == 'SELL':
            return self._check_sell_rule(candle_data)
        else:
            return {
                'valid': False,
                'reason': f'Invalid direction: {direction}',
                'strength': 'INVALID',
                'rules_passed': 0
            }
    
    def _check_buy_rule(self, candle_data):
        """Check 2-candle rule for BUY"""
        c1 = candle_data.get('candle1', {})
        c2 = candle_data.get('candle2', {})
        
        rules_passed = 0
        reasons = []
        
        # Rule 1: First candle is RED (close < open)
        if c1.get('close', 0) < c1.get('open', 1):
            rules_passed += 1
        else:
            reasons.append("First candle should be RED (close < open)")
        
        # Rule 2: Second candle is GREEN (close > open)
        if c2.get('close', 0) > c2.get('open', 1):
            rules_passed += 1
        else:
            reasons.append("Second candle should be GREEN (close > open)")
        
        # Rule 3: Green candle closes ABOVE red candle high
        if c2.get('close', 0) > c1.get('high', 0):
            rules_passed += 1
        else:
            reasons.append(f"Green close ({c2.get('close')}) should be above red high ({c1.get('high')})")
        
        # Determine result
        if rules_passed == 3:
            return {
                'valid': True,
                'reason': '✅ 2-Candle Bullish Reversal confirmed!',
                'strength': 'STRONG',
                'rules_passed': rules_passed,
                'details': f"Red: {c1.get('open')}→{c1.get('close')}, Green: {c2.get('open')}→{c2.get('close')}, Green closed above red high"
            }
        elif rules_passed == 2:
            return {
                'valid': True,
                'reason': '⚠️ 2-Candle Bullish Reversal - Moderate strength',
                'strength': 'MODERATE',
                'rules_passed': rules_passed,
                'details': f"Passed {rules_passed}/3 rules. Issues: {', '.join(reasons)}"
            }
        else:
            return {
                'valid': False,
                'reason': '❌ 2-Candle Rule not satisfied',
                'strength': 'WEAK',
                'rules_passed': rules_passed,
                'details': f"Passed {rules_passed}/3 rules. Issues: {', '.join(reasons)}"
            }
    
    def _check_sell_rule(self, candle_data):
        """Check 2-candle rule for SELL"""
        c1 = candle_data.get('candle1', {})
        c2 = candle_data.get('candle2', {})
        
        rules_passed = 0
        reasons = []
        
        # Rule 1: First candle is GREEN (close > open)
        if c1.get('close', 0) > c1.get('open', 1):
            rules_passed += 1
        else:
            reasons.append("First candle should be GREEN (close > open)")
        
        # Rule 2: Second candle is RED (close < open)
        if c2.get('close', 0) < c2.get('open', 1):
            rules_passed += 1
        else:
            reasons.append("Second candle should be RED (close < open)")
        
        # Rule 3: Red candle closes BELOW green candle low
        if c2.get('close', 0) < c1.get('low', 0):
            rules_passed += 1
        else:
            reasons.append(f"Red close ({c2.get('close')}) should be below green low ({c1.get('low')})")
        
        # Determine result
        if rules_passed == 3:
            return {
                'valid': True,
                'reason': '✅ 2-Candle Bearish Reversal confirmed!',
                'strength': 'STRONG',
                'rules_passed': rules_passed,
                'details': f"Green: {c1.get('open')}→{c1.get('close')}, Red: {c2.get('open')}→{c2.get('close')}, Red closed below green low"
            }
        elif rules_passed == 2:
            return {
                'valid': True,
                'reason': '⚠️ 2-Candle Bearish Reversal - Moderate strength',
                'strength': 'MODERATE',
                'rules_passed': rules_passed,
                'details': f"Passed {rules_passed}/3 rules. Issues: {', '.join(reasons)}"
            }
        else:
            return {
                'valid': False,
                'reason': '❌ 2-Candle Rule not satisfied',
                'strength': 'WEAK',
                'rules_passed': rules_passed,
                'details': f"Passed {rules_passed}/3 rules. Issues: {', '.join(reasons)}"
            }
    
    def get_visual_example(self, direction):
        """Return visual example of the pattern"""
        if direction.upper() == 'BUY':
            return """
            BUY Pattern (2-Candle Rule):
            
            Candle 1: 🔴 RED
              Open:  17.0480
              High:  17.0485
              Low:   17.0460  
              Close: 17.0470  ✗
            
            Candle 2: 🟢 GREEN  
              Open:  17.0470
              High:  17.0490  ✓
              Low:   17.0465
              Close: 17.0485  ✓
            
            ✅ GREEN closes ABOVE red high (17.0485 > 17.0485)
            """
        else:
            return """
            SELL Pattern (2-Candle Rule):
            
            Candle 1: 🟢 GREEN
              Open:  17.0580
              High:  17.0590
              Low:   17.0560  
              Close: 17.0585  ✗
            
            Candle 2: 🔴 RED  
              Open:  17.0585
              High:  17.0588
              Low:   17.0550  ✓
              Close: 17.0555  ✓
            
            ✅ RED closes BELOW green low (17.0555 < 17.0560)
            """
    
    def get_simple_instructions(self, direction):
        """Get simple instructions for the pattern"""
        if direction.upper() == 'BUY':
            return {
                'step1': 'Wait for price to reach support zone',
                'step2': 'Look for a RED candle forming',
                'step3': 'Wait for NEXT candle to be GREEN',
                'step4': 'Confirm GREEN closes ABOVE red high',
                'step5': 'Enter trade after confirmation',
                'warning': 'Do not enter during red candle'
            }
        else:
            return {
                'step1': 'Wait for price to reach resistance zone',
                'step2': 'Look for a GREEN candle forming',
                'step3': 'Wait for NEXT candle to be RED',
                'step4': 'Confirm RED closes BELOW green low',
                'step5': 'Enter trade after confirmation',
                'warning': 'Do not enter during green candle'
            }
