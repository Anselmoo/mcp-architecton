"""Tests for architectures service module."""

import unittest

from mcp_architecton.services.architectures import (
    analyze_architectures_impl,
    list_architectures_impl,
)


class TestArchitecturesService(unittest.TestCase):
    """Test the architectures service functionality."""

    def test_list_architectures_basic(self) -> None:
        """Test basic architecture listing functionality."""
        result = list_architectures_impl()
        self.assertIsInstance(result, list)
        # Should return actual architectures from catalog if available

    def test_analyze_architectures_no_input(self) -> None:
        """Test that providing neither code nor files returns an error."""
        result = analyze_architectures_impl()
        self.assertIn("error", result)
        self.assertIn("Provide 'code' or 'files'", result["error"])

    def test_analyze_architectures_with_code(self) -> None:
        """Test analyzing architectures with code input."""
        sample_code = """
class UserService:
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def create_user(self, user_data):
        return self.user_repo.save(user_data)

class UserRepository:
    def save(self, data):
        pass
"""
        result = analyze_architectures_impl(code=sample_code)
        self.assertIn("findings", result)
        self.assertIsInstance(result["findings"], list)

    def test_analyze_architectures_with_files(self) -> None:
        """Test analyzing architectures with file input."""
        result = analyze_architectures_impl(files=["nonexistent.py"])
        self.assertIn("findings", result)
        # Should handle file read errors gracefully

    def test_analyze_architectures_both_code_and_files(self) -> None:
        """Test analyzing both code and files."""
        sample_code = "class Service: pass"
        result = analyze_architectures_impl(code=sample_code, files=["test.py"])
        self.assertIn("findings", result)

    def test_analyze_architectures_complex_code(self) -> None:
        """Test analyzing more complex architectural patterns."""
        complex_code = """
class UserController:
    def __init__(self, user_service):
        self.user_service = user_service
    
    def create_user(self, request):
        return self.user_service.create_user(request.data)

class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def create_user(self, user_data):
        # Business logic here
        return self.user_repository.save(user_data)

class UserRepository:
    def save(self, data):
        # Data persistence logic
        pass
"""
        result = analyze_architectures_impl(code=complex_code)
        self.assertIn("findings", result)
        self.assertIsInstance(result["findings"], list)


if __name__ == "__main__":
    unittest.main()
