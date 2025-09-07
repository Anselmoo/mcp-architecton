"""Tests for mcp_architecton.services.scan module."""

import unittest
from unittest.mock import patch

from mcp_architecton.services.scan import scan_anti_patterns_impl


class TestScanAntiPatterns(unittest.TestCase):
    """Test the scan_anti_patterns_impl function."""

    def test_no_input_returns_error(self):
        """Test that providing neither code nor files returns an error."""
        result = scan_anti_patterns_impl()
        self.assertIn("error", result)
        self.assertIn("Provide 'code' or 'files'", result["error"])

    def test_code_with_simple_content(self):
        """Test scanning simple code content."""
        simple_code = """
def hello_world():
    print("Hello, world!")
    return "greeting"
"""
        result = scan_anti_patterns_impl(code=simple_code)

        self.assertIn("results", result)
        self.assertIsInstance(result["results"], list)
        self.assertEqual(len(result["results"]), 1)

        # Check that the result has expected structure
        first_result = result["results"][0]
        self.assertIn("source", first_result)
        self.assertIn("metrics", first_result)
        self.assertIn("indicators", first_result)
        self.assertIn("recommendations", first_result)

    def test_code_with_high_complexity_indicators(self):
        """Test code that should trigger anti-pattern indicators."""
        complex_code = """
def complex_function(x):
    # This creates multiple branches to increase complexity
    if x > 10:
        if x > 20:
            if x > 30:
                if x > 40:
                    if x > 50:
                        if x > 60:
                            if x > 70:
                                return "very high"
                            return "high"
                        return "medium-high"
                    return "medium"
                return "low-medium"
            return "low"
        return "very low"
    return "minimal"
"""
        result = scan_anti_patterns_impl(code=complex_code)

        # Should have results
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)

        first_result = result["results"][0]
        indicators = first_result.get("indicators", [])

        # Should detect high complexity
        high_cc_indicators = [ind for ind in indicators if ind.get("type") == "high_cc"]
        self.assertTrue(len(high_cc_indicators) > 0, "Should detect high cyclomatic complexity")

    def test_code_with_print_statements(self):
        """Test code with print statements should trigger logging recommendation."""
        code_with_print = """
def debug_function():
    print("Debug message")
    print("Another debug message")
    return True
"""
        result = scan_anti_patterns_impl(code=code_with_print)

        first_result = result["results"][0]
        indicators = first_result.get("indicators", [])

        # Should detect print statement usage
        print_indicators = [ind for ind in indicators if ind.get("type") == "print_logging"]
        self.assertTrue(len(print_indicators) > 0, "Should detect print statement usage")

    def test_code_with_eval_usage(self):
        """Test code with eval/exec should trigger security recommendation."""
        dangerous_code = """
def dangerous_function(code_string):
    result = eval(code_string)
    return result
"""
        result = scan_anti_patterns_impl(code=dangerous_code)

        first_result = result["results"][0]
        indicators = first_result.get("indicators", [])

        # Should detect eval usage
        eval_indicators = [ind for ind in indicators if ind.get("type") == "dynamic_eval"]
        self.assertTrue(len(eval_indicators) > 0, "Should detect eval usage")

    def test_large_file_detection(self):
        """Test detection of large files."""
        # Create a large code string (over 1000 lines)
        large_code = "# Large file\n" + "def function_{}(): pass\n" * 1500

        result = scan_anti_patterns_impl(code=large_code)

        first_result = result["results"][0]
        indicators = first_result.get("indicators", [])

        # Should detect large file
        large_file_indicators = [ind for ind in indicators if ind.get("type") == "large_file"]
        self.assertTrue(len(large_file_indicators) > 0, "Should detect large file")

    def test_file_reading_error_handling(self):
        """Test that file reading errors are handled gracefully."""
        result = scan_anti_patterns_impl(files=["non_existent_file.py"])

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)

        # Should handle read error gracefully
        first_result = result["results"][0]
        self.assertIn("source", first_result)
        self.assertTrue("non_existent_file.py" in first_result["source"])

    @patch("mcp_architecton.services.scan.cc_visit")
    def test_radon_import_error_handling(self, mock_cc_visit):
        """Test graceful handling when radon is not available."""
        # This test ensures the try-except around radon imports works correctly
        simple_code = "def test(): pass"

        # Mock the import failure by patching the module imports at the top level
        with patch.dict("sys.modules", {"radon": None}):
            # The function should handle import errors gracefully
            result = scan_anti_patterns_impl(code=simple_code)
            # With our current implementation, it will return an error about radon
            # This is expected behavior for missing dependencies
            self.assertTrue("error" in result)

    def test_empty_code_handling(self):
        """Test handling of empty code."""
        result = scan_anti_patterns_impl(code="# empty")  # Need non-empty string

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)

        first_result = result["results"][0]
        self.assertIn("source", first_result)
        self.assertIn("metrics", first_result)

    def test_very_large_function_detection(self):
        """Test detection of very large functions."""
        # Create a function with many lines
        large_function_code = (
            """
def very_large_function():
"""
            + "    # Comment line\n" * 90
        )  # Creates a function with >80 lines

        result = scan_anti_patterns_impl(code=large_function_code)

        first_result = result["results"][0]
        indicators = first_result.get("indicators", [])

        # Should detect very large function
        large_func_indicators = [
            ind for ind in indicators if ind.get("type") == "very_large_function"
        ]
        self.assertTrue(len(large_func_indicators) > 0, "Should detect very large function")


if __name__ == "__main__":
    unittest.main()
