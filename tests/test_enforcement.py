"""Tests for enforcement module."""

import unittest

from mcp_architecton.analysis.enforcement import _simplify, ranked_enforcement_targets


class TestEnforcement(unittest.TestCase):
    """Test the enforcement ranking functionality."""

    def test_simplify_function(self) -> None:
        """Test the _simplify function."""
        self.assertEqual(_simplify("Factory Method"), "factorymethod")
        self.assertEqual(_simplify("Singleton-Pattern"), "singletonpattern")
        self.assertEqual(_simplify("Test_123"), "test123")
        self.assertEqual(_simplify("UPPER case"), "uppercase")
        self.assertEqual(_simplify(""), "")

    def test_ranked_enforcement_targets_empty(self) -> None:
        """Test ranked enforcement with empty inputs."""
        result = ranked_enforcement_targets([], [], {}, {}, {})
        self.assertEqual(result, [])

    def test_ranked_enforcement_targets_basic(self) -> None:
        """Test basic ranked enforcement functionality."""
        indicators = [
            {"type": "high_cc", "weight": 5},
            {"type": "large_file", "weight": 3},
        ]
        recommendations = ["Factory", "Singleton", "Strategy"]
        pattern_advice = {"Factory": "Use factory pattern", "Singleton": "Use singleton"}
        arch_advice = {"Layered": "Use layered architecture"}
        aliases = {"Factory Method": "Factory"}

        result = ranked_enforcement_targets(
            indicators,
            recommendations,
            pattern_advice,
            arch_advice,
            aliases,
        )
        self.assertIsInstance(result, list)
        # Should return list of tuples: (name, category, weight, reasons)
        if result:
            self.assertEqual(len(result[0]), 4)

    def test_ranked_enforcement_targets_with_patterns(self) -> None:
        """Test enforcement with pattern recommendations."""
        indicators = [{"type": "repeated_code", "weight": 8}]
        recommendations = ["Template Method", "Strategy Pattern", "Factory Method"]
        pattern_advice = {
            "Template Method": "Use template method pattern",
            "Strategy": "Use strategy pattern",
            "Factory": "Use factory pattern",
        }
        arch_advice = {}
        aliases = {"Strategy Pattern": "Strategy", "Factory Method": "Factory"}

        result = ranked_enforcement_targets(
            indicators,
            recommendations,
            pattern_advice,
            arch_advice,
            aliases,
        )
        self.assertIsInstance(result, list)
        # Results should be sorted by weight (descending)
        if len(result) > 1:
            self.assertGreaterEqual(result[0][2], result[1][2])

    def test_ranked_enforcement_targets_architecture(self) -> None:
        """Test enforcement with architecture recommendations."""
        indicators = [{"type": "coupling", "weight": 6}]
        recommendations = ["Layered Architecture", "Hexagonal", "Clean Architecture"]
        pattern_advice = {}
        arch_advice = {
            "Layered": "Use layered architecture",
            "Hexagonal": "Use hexagonal architecture",
            "Clean": "Use clean architecture",
        }
        aliases = {"Layered Architecture": "Layered", "Clean Architecture": "Clean"}

        result = ranked_enforcement_targets(
            indicators,
            recommendations,
            pattern_advice,
            arch_advice,
            aliases,
        )
        self.assertIsInstance(result, list)

    def test_ranked_enforcement_targets_mixed(self) -> None:
        """Test enforcement with mixed pattern and architecture recommendations."""
        indicators = [
            {"type": "complexity", "weight": 7},
            {"type": "coupling", "weight": 4},
        ]
        recommendations = ["Factory", "Strategy", "Layered Architecture", "CQRS"]
        pattern_advice = {"Factory": "Factory advice", "Strategy": "Strategy advice"}
        arch_advice = {"Layered": "Layered advice", "CQRS": "CQRS advice"}
        aliases = {"Layered Architecture": "Layered"}

        result = ranked_enforcement_targets(
            indicators,
            recommendations,
            pattern_advice,
            arch_advice,
            aliases,
        )
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
