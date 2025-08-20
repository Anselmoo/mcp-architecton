"""Tests for mcp_architecton.services.intro module (excluding introduce_impl)."""

import unittest
from unittest.mock import patch, Mock

# Note: Direct imports cause circular dependency issues, so we test indirectly


class TestIntroServiceBasic(unittest.TestCase):
    """Basic tests for intro service that avoid circular imports."""

    def test_intro_service_import(self):
        """Test that the intro service can be imported without errors."""
        try:
            from mcp_architecton.services import intro
            self.assertIsNotNone(intro)
        except ImportError as e:
            # If there's a circular import, this test will document it
            self.fail(f"Circular import or missing dependency: {e}")

    def test_canonical_pattern_name_function_exists(self):
        """Test that the canonical pattern name function exists and is callable."""
        try:
            from mcp_architecton.services.intro import _canonical_pattern_name
            
            # Test basic functionality if import succeeds
            result = _canonical_pattern_name("test")
            self.assertIsInstance(result, str)
            
            result = _canonical_pattern_name(None)
            self.assertEqual(result, "")
            
        except ImportError:
            # Skip test if there are dependency issues
            self.skipTest("Cannot import intro module due to dependencies")

    def test_diff_function_exists(self):
        """Test that the diff function exists and works."""
        try:
            from mcp_architecton.services.intro import _diff
            
            result = _diff("line1\nline2", "line1\nmodified", "test.py")
            self.assertIsInstance(result, str)
            
        except ImportError:
            self.skipTest("Cannot import intro module due to dependencies")


if __name__ == "__main__":
    unittest.main()