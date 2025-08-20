"""Tests for mcp_architecton.services.patterns module."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp_architecton.services.patterns import analyze_patterns_impl, list_patterns_impl


class TestListPatterns(unittest.TestCase):
    """Test the list_patterns_impl function."""

    def test_list_patterns_no_catalog(self):
        """Test behavior when catalog file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = list_patterns_impl()
            self.assertEqual(result, [])

    def test_list_patterns_valid_catalog(self):
        """Test listing patterns from a valid catalog file."""
        catalog_data = {
            "patterns": [
                {"name": "Strategy", "category": "Behavioral", "description": "Define a family of algorithms"},
                {"name": "Singleton", "category": "Creational", "description": "Ensure single instance"},
                {"name": "Layered", "category": "Architecture", "description": "Layer-based organization"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(catalog_data, tmp)
            tmp.flush()
            
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.read_text', return_value=json.dumps(catalog_data)):
                result = list_patterns_impl()
                
                # Should exclude Architecture category
                self.assertEqual(len(result), 2)
                names = [p['name'] for p in result]
                self.assertIn("Strategy", names)
                self.assertIn("Singleton", names)
                self.assertNotIn("Layered", names)
        
        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)

    def test_list_patterns_invalid_json(self):
        """Test behavior with invalid JSON catalog."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value='invalid json'):
            result = list_patterns_impl()
            self.assertEqual(result, [])

    def test_list_patterns_no_patterns_key(self):
        """Test behavior when catalog doesn't have patterns key."""
        catalog_data = {"other_data": []}
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=json.dumps(catalog_data)):
            result = list_patterns_impl()
            self.assertEqual(result, [])

    def test_list_patterns_empty_catalog(self):
        """Test behavior with empty catalog."""
        catalog_data = {"patterns": []}
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=json.dumps(catalog_data)):
            result = list_patterns_impl()
            self.assertEqual(result, [])


class TestAnalyzePatterns(unittest.TestCase):
    """Test the analyze_patterns_impl function."""

    def test_analyze_patterns_no_input(self):
        """Test that providing neither code nor files returns an error."""
        result = analyze_patterns_impl()
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Provide 'code' or 'files'")

    @patch('mcp_architecton.services.patterns.analyze_code_for_patterns')
    def test_analyze_patterns_with_code(self, mock_analyze):
        """Test analyzing patterns in provided code."""
        mock_analyze.return_value = [
            {"pattern": "Strategy", "confidence": 0.8, "location": "line 10"}
        ]
        
        test_code = """
class Strategy:
    def execute(self):
        pass

class ConcreteStrategy(Strategy):
    def execute(self):
        return "executed"
"""
        
        result = analyze_patterns_impl(code=test_code)
        
        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 1)
        
        finding = result["findings"][0]
        self.assertEqual(finding["source"], "<input>")
        self.assertEqual(finding["pattern"], "Strategy")
        self.assertEqual(finding["confidence"], 0.8)
        
        # Verify the analysis function was called
        mock_analyze.assert_called_once()

    @patch('mcp_architecton.services.patterns.analyze_code_for_patterns')
    def test_analyze_patterns_with_files(self, mock_analyze):
        """Test analyzing patterns in files."""
        mock_analyze.return_value = [
            {"pattern": "Singleton", "confidence": 0.9, "location": "line 5"}
        ]
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("class Singleton: pass")
            tmp.flush()
            
            result = analyze_patterns_impl(files=[tmp.name])
            
            self.assertIn("findings", result)
            self.assertEqual(len(result["findings"]), 1)
            
            finding = result["findings"][0]
            self.assertEqual(finding["source"], tmp.name)
            self.assertEqual(finding["pattern"], "Singleton")
        
        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)

    @patch('mcp_architecton.services.patterns.analyze_code_for_patterns')
    def test_analyze_patterns_with_code_and_files(self, mock_analyze):
        """Test analyzing both code and files."""
        mock_analyze.return_value = [
            {"pattern": "Observer", "confidence": 0.7}
        ]
        
        test_code = "class Observer: pass"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("class Subject: pass")
            tmp.flush()
            
            result = analyze_patterns_impl(code=test_code, files=[tmp.name])
            
            self.assertIn("findings", result)
            self.assertEqual(len(result["findings"]), 2)  # One for code, one for file
            
            sources = [f["source"] for f in result["findings"]]
            self.assertIn("<input>", sources)
            self.assertIn(tmp.name, sources)
            
            # Verify both entries have the expected pattern
            patterns = [f.get("pattern") for f in result["findings"]]
            self.assertEqual(patterns, ["Observer", "Observer"])
        
        Path(tmp.name).unlink(missing_ok=True)

    def test_analyze_patterns_file_read_error(self):
        """Test handling of file read errors."""
        result = analyze_patterns_impl(files=["nonexistent_file.py"])
        
        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 1)
        
        # Should handle the error gracefully but still try to analyze
        finding = result["findings"][0]
        self.assertEqual(finding["source"], "nonexistent_file.py")

    @patch('mcp_architecton.services.patterns.analyze_code_for_patterns')
    def test_analyze_patterns_analysis_error(self, mock_analyze):
        """Test handling of analysis errors."""
        mock_analyze.side_effect = Exception("Analysis failed")
        
        result = analyze_patterns_impl(code="def test(): pass")
        
        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 1)
        
        finding = result["findings"][0]
        self.assertIn("error", finding)
        self.assertEqual(finding["error"], "Analysis failed")

    @patch('mcp_architecton.services.patterns.analyze_code_for_patterns')
    def test_analyze_patterns_empty_results(self, mock_analyze):
        """Test behavior when analysis returns no patterns."""
        mock_analyze.return_value = []
        
        result = analyze_patterns_impl(code="# empty file")
        
        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 0)

    @patch('mcp_architecton.services.patterns.analyze_code_for_patterns')
    def test_analyze_patterns_multiple_results(self, mock_analyze):
        """Test handling of multiple pattern detections."""
        mock_analyze.return_value = [
            {"pattern": "Strategy", "confidence": 0.8},
            {"pattern": "Factory", "confidence": 0.6},
            {"pattern": "Observer", "confidence": 0.9}
        ]
        
        result = analyze_patterns_impl(code="complex code with multiple patterns")
        
        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 3)
        
        patterns = [f["pattern"] for f in result["findings"]]
        self.assertIn("Strategy", patterns)
        self.assertIn("Factory", patterns)
        self.assertIn("Observer", patterns)
        
        # All should have the same source
        sources = [f["source"] for f in result["findings"]]
        self.assertTrue(all(s == "<input>" for s in sources))


if __name__ == "__main__":
    unittest.main()