"""Tests for typehint_transformer module."""

import unittest

from mcp_architecton.analysis.typehint_transformer import add_type_hints_to_code


class TestTypeHintTransformer(unittest.TestCase):
    """Test the add_type_hints_to_code function."""

    def test_add_type_hints_to_function_without_annotations(self) -> None:
        """Test adding type hints to function without annotations."""
        source = """
def test_function(param):
    return param + 1
"""
        changed, result = add_type_hints_to_code(source)
        self.assertTrue(changed)
        self.assertIn("Any", result)
        self.assertIn("from typing import Any", result)
        self.assertIn("param: Any", result)
        self.assertIn("-> Any", result)

    def test_add_type_hints_skips_self_and_cls(self) -> None:
        """Test that self and cls parameters are not annotated."""
        source = """
class TestClass:
    def method(self, param):
        return param
    
    @classmethod 
    def class_method(cls, param):
        return param
"""
        changed, result = add_type_hints_to_code(source)
        self.assertTrue(changed)
        self.assertNotIn("self: Any", result)
        self.assertNotIn("cls: Any", result)
        self.assertIn("param: Any", result)

    def test_add_type_hints_skips_init_return(self) -> None:
        """Test that __init__ methods don't get return annotations."""
        source = """
class TestClass:
    def __init__(self, param):
        self.param = param
"""
        changed, result = add_type_hints_to_code(source)
        self.assertTrue(changed)
        self.assertIn("param: Any", result)
        self.assertNotIn("def __init__(self, param: Any) -> Any", result)
        self.assertIn("def __init__(self, param: Any)", result)

    def test_no_changes_for_annotated_code(self) -> None:
        """Test that already annotated code is not changed."""
        source = """
def annotated_function(param: str) -> int:
    return len(param)
"""
        changed, result = add_type_hints_to_code(source)
        self.assertFalse(changed)
        self.assertEqual(result, source)

    def test_invalid_syntax_returns_original(self) -> None:
        """Test that invalid syntax returns original code unchanged."""
        source = "invalid python syntax !!!"
        changed, result = add_type_hints_to_code(source)
        self.assertFalse(changed)
        self.assertEqual(result, source)

    def test_mixed_annotated_and_unannotated(self) -> None:
        """Test handling of mixed annotated and unannotated functions."""
        source = """
def annotated(param: str) -> int:
    return len(param)

def unannotated(param):
    return param
"""
        changed, result = add_type_hints_to_code(source)
        self.assertTrue(changed)
        self.assertIn("def annotated(param: str) -> int:", result)
        self.assertIn("def unannotated(param: Any) -> Any:", result)


if __name__ == "__main__":
    unittest.main()
