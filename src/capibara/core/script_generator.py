"""Script generation using LLM providers."""

from typing import Any

from capibara.llm_providers.fallback_manager import FallbackManager
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class ScriptGenerator:
    """Generates executable scripts from processed prompts using LLM providers."""

    def __init__(self, fallback_manager: FallbackManager):
        self.fallback_manager = fallback_manager
        self.last_provider_used: str | None = None
        self.generation_stats = {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "provider_usage": {},
        }

    async def generate(
        self,
        prompt: str,
        language: str,
        provider_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate script code from a processed prompt."""
        logger.info("Generating script", language=language, provider=provider_name)

        self.generation_stats["total_generations"] += 1

        try:
            # Get LLM provider
            provider = await self.fallback_manager.get_provider(provider_name)
            self.last_provider_used = provider.name

            # Build generation prompt
            generation_prompt = self._build_generation_prompt(
                prompt, language, **kwargs
            )

            # Generate code
            code = await provider.generate_code(
                prompt=generation_prompt, language=language, **kwargs
            )

            # Validate generated code
            validated_code = self._validate_generated_code(code, language)

            # Update stats
            self.generation_stats["successful_generations"] += 1
            self.generation_stats["provider_usage"][provider.name] = (
                self.generation_stats["provider_usage"].get(provider.name, 0) + 1
            )

            logger.info(
                "Script generated successfully",
                provider=provider.name,
                code_length=len(validated_code),
            )

            return validated_code

        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(
                "Script generation failed", error=str(e), provider=provider_name
            )
            raise ScriptGenerationError(f"Failed to generate script: {str(e)}") from e

    def _build_generation_prompt(
        self, prompt: str, language: str, **kwargs: Any
    ) -> str:
        """Build the prompt for LLM code generation."""
        language_instructions = self._get_language_instructions(language)

        generation_prompt = f"""
Generate a {language} script that accomplishes the following task:

{prompt}

{language_instructions}

Requirements:
- Write clean, production-ready code
- Include proper error handling
- Add appropriate comments
- Use best practices for {language}
- Make the code safe and secure
- Include input validation where needed
- Add logging for important operations
- Create a function that accepts parameters (don't hardcode specific values)
- Include a main section that demonstrates the function with example usage

Return only the executable code, no explanations or markdown formatting.
"""

        # Add any additional context from kwargs
        if "context" in kwargs:
            generation_prompt += f"\n\nAdditional context: {kwargs['context']}"

        return generation_prompt.strip()

    def _get_language_instructions(self, language: str) -> str:
        """Get language-specific instructions."""
        instructions = {
            "python": """
Python-specific requirements:
- Use type hints where appropriate
- Follow PEP 8 style guidelines
- Use pathlib for file operations
- Handle exceptions gracefully
- Use logging instead of print statements
- Include docstrings for functions
""",
            "javascript": """
JavaScript-specific requirements:
- Use modern ES6+ syntax
- Include proper error handling with try-catch
- Use const/let instead of var
- Add JSDoc comments for functions
- Use async/await for asynchronous operations
- Validate inputs before processing
""",
            "bash": """
Bash-specific requirements:
- Use set -euo pipefail for error handling
- Quote all variables properly
- Use functions for reusable code
- Add comments explaining complex logic
- Check for required commands before using them
- Use proper exit codes
""",
            "powershell": """
PowerShell-specific requirements:
- Use proper error handling with try-catch
- Use Write-Output instead of Write-Host for data
- Include parameter validation
- Use proper variable scoping
- Add comment-based help for functions
- Use approved verbs for function names
""",
        }

        return instructions.get(language.lower(), "")

    def _validate_generated_code(self, code: str, language: str) -> str:
        """Validate and clean generated code."""
        if not code or not code.strip():
            raise ScriptGenerationError("Generated code is empty")

        # Remove markdown code blocks if present
        cleaned_code = self._remove_markdown_blocks(code)

        # Basic syntax validation
        if language.lower() == "python":
            self._validate_python_syntax(cleaned_code)
        elif language.lower() == "javascript":
            self._validate_javascript_syntax(cleaned_code)

        return cleaned_code

    def _remove_markdown_blocks(self, code: str) -> str:
        """Remove markdown code blocks from generated code."""
        import re

        # Remove ```language blocks
        code = re.sub(r"^```\w*\n", "", code, flags=re.MULTILINE)
        code = re.sub(r"\n```$", "", code, flags=re.MULTILINE)

        # Remove ``` blocks
        code = re.sub(r"^```\n", "", code, flags=re.MULTILINE)
        code = re.sub(r"\n```$", "", code, flags=re.MULTILINE)

        return code.strip()

    def _validate_python_syntax(self, code: str) -> None:
        """Basic Python syntax validation."""
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            raise ScriptGenerationError(f"Invalid Python syntax: {e}") from e

    def _validate_javascript_syntax(self, code: str) -> None:
        """Basic JavaScript syntax validation."""
        # This is a simplified check - in production, you'd use a proper JS parser
        if code.count("{") != code.count("}"):
            raise ScriptGenerationError("Unmatched braces in JavaScript code")

        if code.count("(") != code.count(")"):
            raise ScriptGenerationError("Unmatched parentheses in JavaScript code")

    def get_generation_stats(self) -> dict[str, Any]:
        """Get generation statistics."""
        total = self.generation_stats["total_generations"]
        success_rate = (
            self.generation_stats["successful_generations"] / total * 100
            if total > 0
            else 0
        )

        return {
            **self.generation_stats,
            "success_rate_percent": round(success_rate, 2),
        }


class ScriptGenerationError(Exception):
    """Raised when script generation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
