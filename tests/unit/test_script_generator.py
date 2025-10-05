"""Unit tests for Script Generator."""

from unittest.mock import AsyncMock, Mock

import pytest

from capibara.core.script_generator import ScriptGenerationError, ScriptGenerator


class TestScriptGenerator:
    """Test cases for ScriptGenerator."""

    @pytest.fixture
    def mock_fallback_manager(self):
        """Create mock fallback manager."""
        manager = Mock()
        provider = Mock()
        provider.name = "openai"
        provider.generate_code = AsyncMock(return_value="print('Hello, World!')")
        manager.get_provider = AsyncMock(return_value=provider)
        return manager

    @pytest.fixture
    def script_generator(self, mock_fallback_manager):
        """Create ScriptGenerator instance."""
        return ScriptGenerator(mock_fallback_manager)

    @pytest.mark.asyncio
    async def test_generate_script_success(
        self, script_generator, mock_fallback_manager
    ):
        """Test successful script generation."""
        # Arrange
        prompt = "Create a hello world script"
        language = "python"

        # Act
        result = await script_generator.generate(prompt, language)

        # Assert
        assert result == "print('Hello, World!')"
        mock_fallback_manager.get_provider.assert_called_once()

        # Check stats
        stats = script_generator.get_generation_stats()
        assert stats["total_generations"] == 1
        assert stats["successful_generations"] == 1
        assert stats["failed_generations"] == 0
        assert stats["provider_usage"]["openai"] == 1

    @pytest.mark.asyncio
    async def test_generate_script_with_provider_preference(
        self, script_generator, mock_fallback_manager
    ):
        """Test script generation with specific provider."""
        # Arrange
        prompt = "Create a hello world script"
        language = "python"
        provider_name = "groq"

        # Act
        result = await script_generator.generate(prompt, language, provider_name)

        # Assert
        assert result == "print('Hello, World!')"
        mock_fallback_manager.get_provider.assert_called_once_with(provider_name)

    @pytest.mark.asyncio
    async def test_generate_script_failure(
        self, script_generator, mock_fallback_manager
    ):
        """Test script generation failure."""
        # Arrange
        prompt = "Create a hello world script"
        language = "python"

        # Mock provider failure
        mock_fallback_manager.get_provider.side_effect = Exception("Provider error")

        # Act & Assert
        with pytest.raises(ScriptGenerationError) as exc_info:
            await script_generator.generate(prompt, language)

        assert "Failed to generate script" in str(exc_info.value)

        # Check stats
        stats = script_generator.get_generation_stats()
        assert stats["total_generations"] == 1
        assert stats["successful_generations"] == 0
        assert stats["failed_generations"] == 1

    def test_build_generation_prompt(self, script_generator):
        """Test prompt building."""
        # Arrange
        prompt = "Create a hello world script"
        language = "python"

        # Act
        result = script_generator._build_generation_prompt(prompt, language)

        # Assert
        assert "Generate a python script" in result
        assert prompt in result
        assert "Python-specific requirements" in result
        assert "production-ready code" in result

    def test_get_language_instructions(self, script_generator):
        """Test language-specific instructions."""
        # Test Python
        python_instructions = script_generator._get_language_instructions("python")
        assert "PEP 8" in python_instructions
        assert "type hints" in python_instructions

        # Test JavaScript
        js_instructions = script_generator._get_language_instructions("javascript")
        assert "ES6+" in js_instructions
        assert "async/await" in js_instructions

        # Test Bash
        bash_instructions = script_generator._get_language_instructions("bash")
        assert "pipefail" in bash_instructions
        assert "exit codes" in bash_instructions

        # Test unknown language
        unknown_instructions = script_generator._get_language_instructions("unknown")
        assert unknown_instructions == ""

    def test_validate_generated_code_success(self, script_generator):
        """Test successful code validation."""
        # Arrange
        code = "print('Hello, World!')"
        language = "python"

        # Act
        result = script_generator._validate_generated_code(code, language)

        # Assert
        assert result == code

    def test_validate_generated_code_empty(self, script_generator):
        """Test validation of empty code."""
        # Act & Assert
        with pytest.raises(ScriptGenerationError):
            script_generator._validate_generated_code("", "python")

        with pytest.raises(ScriptGenerationError):
            script_generator._validate_generated_code("   ", "python")

    def test_validate_generated_code_with_markdown(self, script_generator):
        """Test code validation with markdown blocks."""
        # Arrange
        code_with_markdown = "```python\nprint('Hello, World!')\n```"
        language = "python"

        # Act
        result = script_generator._validate_generated_code(code_with_markdown, language)

        # Assert
        assert "```" not in result
        assert "print('Hello, World!')" in result

    def test_validate_python_syntax_error(self, script_generator):
        """Test Python syntax validation with error."""
        # Arrange
        invalid_code = "def broken_function(\n    print('This is broken')"
        language = "python"

        # Act & Assert
        with pytest.raises(ScriptGenerationError) as exc_info:
            script_generator._validate_generated_code(invalid_code, language)

        assert "Invalid Python syntax" in str(exc_info.value)

    def test_validate_javascript_syntax(self, script_generator):
        """Test JavaScript syntax validation."""
        # Test valid JavaScript
        valid_js = "function hello() { console.log('Hello'); }"
        script_generator._validate_javascript_syntax(valid_js)
        # Should not raise exception

        # Test invalid JavaScript (unmatched braces)
        invalid_js = "function hello() { console.log('Hello');"
        with pytest.raises(ScriptGenerationError) as exc_info:
            script_generator._validate_javascript_syntax(invalid_js)

        assert "Unmatched braces" in str(exc_info.value)

        # Test invalid JavaScript (unmatched parentheses)
        invalid_js2 = "function hello( { console.log('Hello'); }"
        with pytest.raises(ScriptGenerationError) as exc_info:
            script_generator._validate_javascript_syntax(invalid_js2)

        assert "Unmatched parentheses" in str(exc_info.value)

    def test_remove_markdown_blocks(self, script_generator):
        """Test markdown block removal."""
        # Test with language block
        code1 = "```python\nprint('Hello')\n```"
        result1 = script_generator._remove_markdown_blocks(code1)
        assert result1 == "print('Hello')"

        # Test with generic block
        code2 = "```\nprint('Hello')\n```"
        result2 = script_generator._remove_markdown_blocks(code2)
        assert result2 == "print('Hello')"

        # Test multiple blocks
        code3 = "```python\nprint('Hello')\n```\n```\nprint('World')\n```"
        result3 = script_generator._remove_markdown_blocks(code3)
        assert "print('Hello')" in result3
        assert "print('World')" in result3
        assert "```" not in result3

    def test_generation_stats(self, script_generator):
        """Test generation statistics."""
        # Initial stats
        stats = script_generator.get_generation_stats()
        assert stats["total_generations"] == 0
        assert stats["successful_generations"] == 0
        assert stats["failed_generations"] == 0
        assert stats["success_rate_percent"] == 0
        assert stats["provider_usage"] == {}

    def test_script_generation_error(self):
        """Test ScriptGenerationError exception."""
        # Test basic error
        error = ScriptGenerationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

        # Test error with details
        details = {"provider": "openai", "model": "gpt-3.5-turbo"}
        error_with_details = ScriptGenerationError("Test error", details)
        assert error_with_details.details == details
