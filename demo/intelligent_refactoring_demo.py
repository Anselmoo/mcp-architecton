#!/usr/bin/env python3
"""
Demonstration of intelligent refactoring capabilities.

This script shows how the enhanced refactoring system works compared 
to simple template appending.
"""

from mcp_architecton.analysis.refactoring_engine import intelligent_refactor


def demo_singleton_refactoring():
    """Demonstrate intelligent singleton refactoring."""
    print("=" * 60)
    print("SINGLETON PATTERN REFACTORING DEMO")
    print("=" * 60)
    
    # Example: Existing class that should become singleton
    original_code = '''
class DatabaseConnection:
    """Handles database connections."""
    
    def __init__(self, host="localhost", port=5432):
        self.host = host
        self.port = port
        self.connection = None
        self.is_connected = False
    
    def connect(self):
        """Establish database connection."""
        if not self.is_connected:
            # Simulate connection logic
            print(f"Connecting to {self.host}:{self.port}")
            self.connection = f"conn_{self.host}_{self.port}"
            self.is_connected = True
        return self.connection
    
    def disconnect(self):
        """Close database connection."""
        if self.is_connected:
            print("Disconnecting from database")
            self.connection = None
            self.is_connected = False
'''
    
    print("ORIGINAL CODE:")
    print(original_code)
    print("\n" + "="*60)
    
    # Use intelligent refactoring
    result = intelligent_refactor(original_code, "singleton")
    
    print("INTELLIGENT REFACTORING ANALYSIS:")
    print("-" * 40)
    
    # Show analysis
    analysis = result.get("analysis", {})
    existing = analysis.get("existing_structure", {})
    print(f"Detected classes: {existing.get('classes', [])}")
    print(f"Detected functions: {existing.get('functions', [])}")
    print(f"Detected patterns: {[p.get('name', '') for p in existing.get('detected_patterns', [])]}")
    
    # Show transformation plan
    print("\nTRANSFORMATION PLAN:")
    print("-" * 40)
    for step in result.get("refactoring_plan", []):
        print(f"Step {step.get('step', '?')}: {step.get('description', 'N/A')}")
        print(f"  Action: {step.get('action', 'N/A')}")
        print(f"  Target: {step.get('target', 'N/A')}")
        print()
    
    # Show step-by-step instructions
    print("STEP-BY-STEP INSTRUCTIONS FOR LLM/COPILOT:")
    print("-" * 40)
    for instruction in result.get("step_by_step_instructions", []):
        print(f"Step {instruction.get('step', '?')}: {instruction.get('description', 'N/A')}")
        print(f"  Code changes needed: {instruction.get('code_changes', {}).get('description', 'See details')}")
        print(f"  Validation: {instruction.get('validation', 'N/A')}")
        print()
    
    # Show risks
    risks = result.get("risks", [])
    if risks:
        print("RISKS AND CONSIDERATIONS:")
        print("-" * 40)
        for risk in risks:
            print(f"• {risk}")
        print()
    
    # Show transformed code if available
    transformation = result.get("transformation_result", {})
    if transformation.get("success") and transformation.get("transformed_code"):
        print("INTELLIGENTLY TRANSFORMED CODE:")
        print("-" * 40)
        print(transformation["transformed_code"])
        print("\nCHANGES MADE:")
        for change in transformation.get("changes_made", []):
            print(f"• {change}")
    else:
        print("No intelligent transformation available")
        print(f"Reason: {transformation.get('reason', 'Unknown')}")


def demo_strategy_refactoring():
    """Demonstrate intelligent strategy refactoring."""
    print("\n" + "=" * 60)
    print("STRATEGY PATTERN REFACTORING DEMO")
    print("=" * 60)
    
    # Example: Payment processing that could benefit from strategy pattern
    original_code = '''
class PaymentProcessor:
    """Process payments using different methods."""
    
    def __init__(self):
        self.processed_payments = []
    
    def process_payment(self, method, amount, details):
        """Process payment based on method."""
        if method == "credit_card":
            return self._process_credit_card(amount, details)
        elif method == "bank_transfer":
            return self._process_bank_transfer(amount, details)
        elif method == "crypto":
            return self._process_crypto(amount, details)
        else:
            raise ValueError(f"Unknown payment method: {method}")
    
    def _process_credit_card(self, amount, details):
        """Process credit card payment."""
        card_number = details.get("card_number", "")
        masked_card = "*" * 12 + card_number[-4:]
        result = {
            "method": "credit_card",
            "amount": amount,
            "card": masked_card,
            "status": "completed"
        }
        self.processed_payments.append(result)
        return result
    
    def _process_bank_transfer(self, amount, details):
        """Process bank transfer payment."""
        account = details.get("account", "")
        result = {
            "method": "bank_transfer", 
            "amount": amount,
            "account": account,
            "status": "pending"
        }
        self.processed_payments.append(result)
        return result
    
    def _process_crypto(self, amount, details):
        """Process cryptocurrency payment."""
        wallet = details.get("wallet", "")
        result = {
            "method": "crypto",
            "amount": amount,
            "wallet": wallet,
            "status": "confirming"
        }
        self.processed_payments.append(result)
        return result
'''
    
    print("ORIGINAL CODE:")
    print(original_code)
    print("\n" + "="*60)
    
    # Use intelligent refactoring 
    result = intelligent_refactor(original_code, "strategy")
    
    print("INTELLIGENT REFACTORING ANALYSIS:")
    print("-" * 40)
    
    # Show analysis
    analysis = result.get("analysis", {})
    existing = analysis.get("existing_structure", {})
    print(f"Detected classes: {existing.get('classes', [])}")
    print(f"Functions that could become strategies: {existing.get('functions', [])}")
    
    # Show opportunities
    opportunities = analysis.get("opportunities", [])
    if opportunities:
        print("\nREFACTORING OPPORTUNITIES DETECTED:")
        for opp in opportunities:
            print(f"• {opp.get('type', 'Unknown')}: {opp.get('reason', 'N/A')}")
    
    # Show transformation plan
    print("\nTRANSFORMATION PLAN:")
    print("-" * 40)
    for step in result.get("refactoring_plan", []):
        print(f"Step {step.get('step', '?')}: {step.get('description', 'N/A')}")
        print(f"  Target: {step.get('target', 'N/A')}")
        print()
    
    # Show transformed code if available
    transformation = result.get("transformation_result", {})
    if transformation.get("success") and transformation.get("transformed_code"):
        print("INTELLIGENTLY TRANSFORMED CODE:")
        print("-" * 40)
        print(transformation["transformed_code"])
        print("\nCHANGES MADE:")
        for change in transformation.get("changes_made", []):
            print(f"• {change}")


def compare_with_traditional():
    """Compare intelligent refactoring with traditional template appending."""
    print("\n" + "=" * 60)
    print("COMPARISON: INTELLIGENT vs TRADITIONAL APPENDING")
    print("=" * 60)
    
    simple_code = '''
class DataManager:
    def load_data(self):
        return "data"
'''
    
    print("SIMPLE ORIGINAL CODE:")
    print(simple_code)
    
    # Traditional approach (would just append template)
    print("\nTRADITIONAL APPROACH (Template Appending):")
    print("-" * 40)
    print("Would blindly append singleton template to end of file")
    print("Result: Two classes, no integration, duplicate code")
    
    # Intelligent approach
    print("\nINTELLIGENT APPROACH:")
    print("-" * 40)
    result = intelligent_refactor(simple_code, "singleton")
    transformation = result.get("transformation_result", {})
    
    if transformation.get("success"):
        print("Analyzes existing code structure")
        print("Transforms existing class to add singleton behavior")
        print("Preserves existing functionality")
        print("Integrates pattern seamlessly")
        
        print("\nTransformed code:")
        print(transformation.get("transformed_code", ""))
    else:
        print("Falls back to traditional approach when transformation not possible")


if __name__ == "__main__":
    demo_singleton_refactoring()
    demo_strategy_refactoring()
    compare_with_traditional()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("The intelligent refactoring system provides:")
    print("• Context-aware analysis of existing code")
    print("• Step-by-step transformation instructions for LLMs")
    print("• Integration with existing code rather than blind appending")
    print("• Risk assessment and validation steps")
    print("• Diff-based suggestions with before/after comparisons")
    print("• Fallback to traditional templates when needed")
    print("\nThis addresses the original issue of LLMs blindly appending")
    print("boilerplate code without understanding existing structure.")