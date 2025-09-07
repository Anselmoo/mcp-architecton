"""Tests for metrics service module."""

import unittest
from unittest.mock import patch, MagicMock

from mcp_architecton.services.metrics import analyze_metrics_impl


class TestMetricsService(unittest.TestCase):
    """Test the metrics service functionality."""

    def test_analyze_metrics_no_input(self) -> None:
        """Test that providing neither code nor files returns an error."""
        result = analyze_metrics_impl()
        self.assertIn("error", result)
        self.assertIn("Provide 'code' or 'files'", result["error"])

    def test_analyze_metrics_with_code(self) -> None:
        """Test analyzing metrics with code input."""
        sample_code = """
def simple_function():
    return "hello"

def complex_function(x):
    if x > 10:
        if x > 20:
            return x * 3
        return x * 2
    return x
"""
        result = analyze_metrics_impl(code=sample_code)
        self.assertIn("results", result)
        self.assertIn("ruff", result)
        self.assertIsInstance(result["results"], list)
        if result["results"]:
            first_result = result["results"][0]
            self.assertIn("source", first_result)
            # The cyclomatic_complexity is a list of complexity data
            self.assertIn("cyclomatic_complexity", first_result)
            self.assertIn("maintainability_index", first_result)

    def test_analyze_metrics_with_files(self) -> None:
        """Test analyzing metrics with file input."""
        # Test with non-existent file
        result = analyze_metrics_impl(files=["nonexistent.py"])
        self.assertIn("results", result)
        # Should handle file read errors gracefully

    def test_analyze_metrics_invalid_code(self) -> None:
        """Test analyzing metrics with invalid Python code."""
        invalid_code = "invalid python syntax!!!"
        result = analyze_metrics_impl(code=invalid_code)
        self.assertIn("results", result)
        # Should handle syntax errors in the result

    def test_analyze_metrics_both_code_and_files(self) -> None:
        """Test analyzing both code and files."""
        sample_code = "def test(): pass"
        result = analyze_metrics_impl(code=sample_code, files=["test.py"])
        self.assertIn("results", result)
        self.assertIn("ruff", result)

    @patch('mcp_architecton.services.metrics.shutil.which')
    def test_analyze_metrics_no_ruff(self, mock_which: MagicMock) -> None:
        """Test behavior when ruff is not available."""
        mock_which.return_value = None
        result = analyze_metrics_impl(code="def test(): pass")
        self.assertIn("ruff", result)
        self.assertIn("error", result["ruff"])
        self.assertIn("not available", result["ruff"]["error"])

    def test_analyze_metrics_complex_code(self) -> None:
        """Test analyzing more complex code for metrics."""
        complex_code = """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self):
        return self.history.copy()
"""
        result = analyze_metrics_impl(code=complex_code)
        self.assertIn("results", result)
        if result["results"]:
            metrics = result["results"][0]
            # cyclomatic_complexity is a list of complexity data
            self.assertIsInstance(metrics.get("cyclomatic_complexity"), list)
            # maintainability_index is a numeric value
            self.assertIsInstance(metrics.get("maintainability_index"), (int, float))


if __name__ == "__main__":
    unittest.main()