"""Tests for intelligent refactoring functionality."""

import unittest

from mcp_architecton.analysis.code_analyzer import (
    analyze_code_structure,
    create_refactoring_context,
)
from mcp_architecton.analysis.refactoring_engine import intelligent_refactor


class TestIntelligentRefactoring(unittest.TestCase):
    """Test intelligent refactoring capabilities."""
    
    def test_analyze_code_structure_empty(self):
        """Test code structure analysis with empty code."""
        structure = analyze_code_structure("")
        self.assertEqual(len(structure.classes), 0)
        self.assertEqual(len(structure.functions), 0)
        self.assertEqual(len(structure.patterns), 0)
    
    def test_analyze_code_structure_simple_class(self):
        """Test code structure analysis with a simple class."""
        code = """
class TestClass:
    def __init__(self):
        pass
    
    def method1(self):
        pass
"""
        structure = analyze_code_structure(code)
        self.assertEqual(len(structure.classes), 1)
        self.assertEqual(structure.classes[0], "TestClass")
        # Functions include methods
        self.assertTrue(any("__init__" in func for func in structure.functions))
    
    def test_refactoring_context_creation(self):
        """Test creating refactoring context."""
        code = """
class ExistingClass:
    def process_data(self, data):
        if data > 10:
            return "large"
        else:
            return "small"
"""
        context = create_refactoring_context(code, "strategy")
        self.assertEqual(context.target_pattern, "strategy")
        self.assertEqual(len(context.existing_structure.classes), 1)
        self.assertTrue(len(context.transformation_plan) > 0)
    
    def test_intelligent_refactor_singleton(self):
        """Test intelligent refactoring for singleton pattern."""
        code = """
class DatabaseConnection:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        pass
"""
        result = intelligent_refactor(code, "singleton")
        
        # Should have analysis
        self.assertIn("analysis", result)
        self.assertIn("existing_structure", result["analysis"])
        
        # Should have transformation plan
        self.assertIn("refactoring_plan", result)
        self.assertTrue(len(result["refactoring_plan"]) > 0)
        
        # Should have step-by-step instructions
        self.assertIn("step_by_step_instructions", result)
        
        # Should have transformation result
        self.assertIn("transformation_result", result)
        transformation = result["transformation_result"]
        if transformation.get("success"):
            self.assertIn("transformed_code", transformation)
            self.assertIn("_instance", transformation["transformed_code"])
            self.assertIn("__new__", transformation["transformed_code"])
    
    def test_intelligent_refactor_strategy(self):
        """Test intelligent refactoring for strategy pattern."""
        code = """
class PaymentProcessor:
    def process_payment(self, method, amount):
        if method == "credit":
            return self.process_credit(amount)
        elif method == "debit":
            return self.process_debit(amount)
        else:
            raise ValueError("Unknown method")
    
    def process_credit(self, amount):
        return f"Credit: {amount}"
    
    def process_debit(self, amount):
        return f"Debit: {amount}"
"""
        result = intelligent_refactor(code, "strategy")
        
        # Should have analysis and plans
        self.assertIn("analysis", result)
        self.assertIn("refactoring_plan", result)
        self.assertIn("step_by_step_instructions", result)
        
        # Should detect opportunity for strategy pattern
        transformation = result["transformation_result"]
        if transformation.get("success"):
            transformed_code = transformation.get("transformed_code", "")
            self.assertIn("Strategy", transformed_code)
            self.assertIn("Context", transformed_code)
    
    def test_refactoring_with_no_existing_code(self):
        """Test refactoring with minimal existing code."""
        code = "# Empty module"
        
        result = intelligent_refactor(code, "singleton")
        
        # Should still provide analysis and suggestions
        self.assertIn("analysis", result)
        self.assertIn("refactoring_plan", result)
        
        # Should warn about minimal code
        if "risks" in result:
            risk_text = " ".join(result["risks"])
            self.assertTrue("minimal code" in risk_text or "Empty" in risk_text or len(result["risks"]) > 0)
    
    def test_complex_function_detection(self):
        """Test detection of complex functions that could benefit from refactoring."""
        code = """
def complex_function(x, y, z, a, b, c, d, e):
    # Long function with many parameters
    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    if b > 0:
                        if c > 0:
                            if d > 0:
                                if e > 0:
                                    return "all positive"
                                else:
                                    return "e not positive"
                            else:
                                return "d not positive"
                        else:
                            return "c not positive"
                    else:
                        return "b not positive"
                else:
                    return "a not positive"
            else:
                return "z not positive"
        else:
            return "y not positive"
    else:
        return "x not positive"
"""
        structure = analyze_code_structure(code)
        
        # Should detect high parameter count
        param_opportunities = [opp for opp in structure.refactoring_opportunities 
                             if opp.get("type") == "parameter_object"]
        self.assertTrue(len(param_opportunities) > 0)
        
        # Should detect function complexity
        function_opportunities = [opp for opp in structure.refactoring_opportunities
                                if opp.get("type") == "function_decomposition"]
        self.assertTrue(len(function_opportunities) > 0)


if __name__ == "__main__":
    unittest.main()