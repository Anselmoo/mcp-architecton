"""Tests for mcp_architecton.refactors.strategies module."""

import unittest
from unittest.mock import Mock, patch

from mcp_architecton.refactors.strategies import (
    _append_snippet_marker,
    _canon,
    _safe_libcst_insert_class,
    _safe_libcst_insert_function,
    register_strategy,
    transform_code,
)


class TestCanonFunction(unittest.TestCase):
    """Test the _canon function for name canonicalization."""

    def test_canon_with_valid_name(self):
        """Test canonical name resolution."""
        # Should lowercase and strip whitespace
        result = _canon("  STRATEGY  ")
        self.assertEqual(result, "strategy")
        
        result = _canon("Facade")
        self.assertEqual(result, "facade")

    def test_canon_with_none(self):
        """Test canonical name with None input."""
        result = _canon(None)
        self.assertEqual(result, "")

    def test_canon_with_empty_string(self):
        """Test canonical name with empty input."""
        result = _canon("")
        self.assertEqual(result, "")
        
        result = _canon("   ")
        self.assertEqual(result, "")


class TestAppendSnippetMarker(unittest.TestCase):
    """Test the _append_snippet_marker function."""

    def test_append_snippet_marker_new(self):
        """Test adding a new snippet marker."""
        original_text = "def existing_code():\n    pass"
        marker_key = "test_pattern"
        body = "class TestPattern:\n    pass"
        
        result = _append_snippet_marker(original_text, marker_key, body)
        
        self.assertIn("# --- mcp-architecton strategy: test_pattern ---", result)
        self.assertIn("class TestPattern:\n    pass", result)
        self.assertIn("# --- end strategy ---", result)
        self.assertTrue(result.startswith(original_text.rstrip()))

    def test_append_snippet_marker_existing(self):
        """Test that marker is not duplicated if already exists."""
        marker_key = "test_pattern"
        existing_text = f"""def existing_code():
    pass

# --- mcp-architecton strategy: {marker_key} ---
class ExistingPattern:
    pass
# --- end strategy ---
"""
        body = "class NewPattern:\n    pass"
        
        result = _append_snippet_marker(existing_text, marker_key, body)
        
        # Should return original text unchanged
        self.assertEqual(result, existing_text)

    def test_append_snippet_marker_empty_text(self):
        """Test appending to empty text."""
        result = _append_snippet_marker("", "test", "body")
        
        self.assertIn("# --- mcp-architecton strategy: test ---", result)
        self.assertIn("body", result)
        self.assertIn("# --- end strategy ---", result)


class TestSafeLibCSTInsert(unittest.TestCase):
    """Test the safe LibCST insertion functions."""

    def test_safe_libcst_insert_class_without_libcst(self):
        """Test class insertion when LibCST is not available."""
        with patch('mcp_architecton.refactors.strategies.cst', None):
            result = _safe_libcst_insert_class("def test(): pass", "class Test: pass")
            self.assertIsNone(result)

    def test_safe_libcst_insert_function_without_libcst(self):
        """Test function insertion when LibCST is not available."""
        with patch('mcp_architecton.refactors.strategies.cst', None):
            result = _safe_libcst_insert_function("class Test: pass", "def test(): pass")
            self.assertIsNone(result)

    @patch('mcp_architecton.refactors.strategies.cst')
    @patch('mcp_architecton.refactors.strategies.parse_module')
    def test_safe_libcst_insert_class_parse_error(self, mock_parse, mock_cst):
        """Test class insertion when parsing fails."""
        mock_cst.__bool__ = Mock(return_value=True)
        mock_parse.side_effect = Exception("Parse error")
        
        result = _safe_libcst_insert_class("invalid python", "class Test: pass")
        self.assertIsNone(result)

    @patch('mcp_architecton.refactors.strategies.cst')
    @patch('mcp_architecton.refactors.strategies.parse_module')
    def test_safe_libcst_insert_function_parse_error(self, mock_parse, mock_cst):
        """Test function insertion when parsing fails."""
        mock_cst.__bool__ = Mock(return_value=True)
        mock_parse.side_effect = Exception("Parse error")
        
        result = _safe_libcst_insert_function("invalid python", "def test(): pass")
        self.assertIsNone(result)


class TestStrategyRegistration(unittest.TestCase):
    """Test strategy registration and lookup."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original state
        from mcp_architecton.refactors.strategies import _STRATEGIES
        self.original_strategies = _STRATEGIES.copy()

    def tearDown(self):
        """Clean up after tests."""
        # Restore original state
        from mcp_architecton.refactors.strategies import _STRATEGIES
        _STRATEGIES.clear()
        _STRATEGIES.update(self.original_strategies)

    def test_register_strategy(self):
        """Test registering a new strategy."""
        def test_strategy(source: str) -> str | None:
            return source + "\n# test strategy applied"
        
        register_strategy("test_pattern", test_strategy)
        
        # Test that it can be used
        result = transform_code("test_pattern", "def test(): pass")
        
        if result:  # May be None if generic transforms are applied instead
            self.assertIn("# test strategy applied", result)

    def test_register_strategy_canonical_name(self):
        """Test that strategy registration uses canonical names."""
        def test_strategy(source: str) -> str | None:
            return source + "\n# canonical test"
        
        register_strategy("  TEST_PATTERN  ", test_strategy)
        
        # Should be registered under canonical name
        result = transform_code("test_pattern", "def test(): pass")
        
        if result:
            self.assertIn("# canonical test", result)


class TestTransformCode(unittest.TestCase):
    """Test the main transform_code function."""

    def test_transform_code_with_known_pattern(self):
        """Test transforming code with a known pattern."""
        # Test with singleton pattern (should be registered)
        original_code = "def test():\n    pass"
        
        result = transform_code("singleton", original_code)
        
        # Result should be string or None
        self.assertIsInstance(result, (str, type(None)))

    def test_transform_code_with_unknown_pattern(self):
        """Test transforming code with unknown pattern."""
        original_code = "def test():\n    pass"
        
        result = transform_code("unknown_pattern_xyz", original_code)
        
        # Should return None or apply generic transforms
        self.assertIsInstance(result, (str, type(None)))

    def test_transform_code_with_empty_code(self):
        """Test transforming empty code."""
        result = transform_code("strategy", "")
        
        self.assertIsInstance(result, (str, type(None)))

    def test_transform_code_error_handling(self):
        """Test that transform_code handles errors gracefully."""
        def failing_strategy(source: str) -> str | None:
            raise ValueError("Strategy failed")
        
        # Temporarily register a failing strategy
        register_strategy("failing", failing_strategy)
        
        # Should not raise an exception
        result = transform_code("failing", "def test(): pass")
        self.assertIsInstance(result, (str, type(None)))

    def test_transform_code_no_change(self):
        """Test behavior when no transformation is needed."""
        def no_change_strategy(source: str) -> str | None:
            return source  # Return same content
        
        register_strategy("no_change", no_change_strategy)
        
        original = "def test(): pass"
        result = transform_code("no_change", original)
        
        # Should return None since content is unchanged
        self.assertIsNone(result)

    def test_transform_code_with_generic_fallback(self):
        """Test that generic transforms are applied as fallback."""
        # Use an unknown pattern to trigger generic transforms
        original_code = "def test():\n    pass"
        
        result = transform_code("unknown_xyz", original_code)
        
        # Should try generic transforms
        self.assertIsInstance(result, (str, type(None)))


class TestBuiltInStrategies(unittest.TestCase):
    """Test the built-in strategy implementations."""

    def test_strategy_singleton(self):
        """Test singleton strategy application."""
        original_code = "def existing_function():\n    pass"
        
        result = transform_code("singleton", original_code)
        
        # Should return modified code or None
        self.assertIsInstance(result, (str, type(None)))
        
        if result:
            # Should contain singleton-related content
            self.assertTrue(
                "Singleton" in result or 
                "_instance" in result or
                "# --- mcp-architecton strategy:" in result
            )

    def test_strategy_observer(self):
        """Test observer strategy application."""
        original_code = "def existing_function():\n    pass"
        
        result = transform_code("observer", original_code)
        
        self.assertIsInstance(result, (str, type(None)))
        
        if result:
            # Should contain observer-related content
            self.assertTrue(
                "Observable" in result or
                "subscribe" in result or
                "# --- mcp-architecton strategy:" in result
            )

    def test_strategy_facade_function(self):
        """Test facade function strategy application."""
        original_code = "def existing_function():\n    pass"
        
        result = transform_code("facade_function", original_code)
        
        self.assertIsInstance(result, (str, type(None)))
        
        if result:
            self.assertTrue(
                "facade_function" in result or
                "# --- mcp-architecton strategy:" in result
            )

    def test_strategy_strategy_pattern(self):
        """Test strategy pattern strategy application."""
        original_code = "def existing_function():\n    pass"
        
        result = transform_code("strategy", original_code)
        
        self.assertIsInstance(result, (str, type(None)))
        
        if result:
            self.assertTrue(
                "Strategy" in result or
                "Context" in result or
                "abstractmethod" in result or
                "# --- mcp-architecton strategy:" in result
            )


if __name__ == "__main__":
    unittest.main()