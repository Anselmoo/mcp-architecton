"""Tests for advice_loader module."""

import unittest
from unittest.mock import MagicMock, patch

from mcp_architecton.analysis.advice_loader import (
    _category_for_name,
    _load_module_for_detector,
    build_advice_maps,
)


class TestAdviceLoader(unittest.TestCase):
    """Test the advice_loader functionality."""

    def test_category_for_name_patterns(self) -> None:
        """Test categorizing pattern names."""
        self.assertEqual(_category_for_name("Factory Method"), "Pattern")
        self.assertEqual(_category_for_name("Singleton"), "Pattern")
        self.assertEqual(_category_for_name("Observer"), "Pattern")
        self.assertEqual(_category_for_name("Strategy"), "Pattern")

    def test_category_for_name_architectures(self) -> None:
        """Test categorizing architecture names."""
        self.assertEqual(_category_for_name("Layered Architecture"), "Architecture")
        self.assertEqual(_category_for_name("Clean Architecture"), "Architecture")
        self.assertEqual(_category_for_name("Hexagonal Architecture"), "Architecture")
        self.assertEqual(_category_for_name("Domain Events"), "Architecture")
        self.assertEqual(_category_for_name("CQRS"), "Architecture")

    def test_category_for_name_unknown(self) -> None:
        """Test categorizing unknown names defaults to Pattern."""
        self.assertEqual(_category_for_name("Unknown Pattern"), "Pattern")
        self.assertEqual(_category_for_name("Random Name"), "Pattern")
        self.assertEqual(_category_for_name(""), "Pattern")

    def test_load_module_for_detector_with_module(self) -> None:
        """Test loading module when detector has a module."""
        mock_detector = MagicMock()
        mock_module = MagicMock()

        with patch("inspect.getmodule", return_value=mock_module):
            result = _load_module_for_detector("test", mock_detector)
            self.assertEqual(result, mock_module)

    def test_load_module_for_detector_fallback(self) -> None:
        """Test fallback module loading when detector has no module."""
        mock_detector = MagicMock()

        with patch("inspect.getmodule", return_value=None), \
             patch("importlib.import_module", side_effect=ImportError()) as mock_import:
            result = _load_module_for_detector("test_pattern", mock_detector)
            self.assertIsNone(result)
            # Should try importing known module paths
            mock_import.assert_called()

    def test_build_advice_maps_basic(self) -> None:
        """Test building advice maps with basic functionality."""
        pattern_advice, arch_advice = build_advice_maps()

        self.assertIsInstance(pattern_advice, dict)
        self.assertIsInstance(arch_advice, dict)


if __name__ == "__main__":
    unittest.main()
