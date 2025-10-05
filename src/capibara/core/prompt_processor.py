"""Prompt processing for natural language to script generation."""

import re
from typing import Any

from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class PromptProcessor:
    """Processes natural language prompts for script generation."""

    def __init__(self) -> None:
        self.prompt_templates = {
            "data_processing": "Process the following data: {prompt}",
            "file_operations": "Perform file operations: {prompt}",
            "api_integration": "Create API integration: {prompt}",
            "data_analysis": "Analyze data: {prompt}",
            "web_scraping": "Scrape web data: {prompt}",
            "automation": "Automate task: {prompt}",
        }

    async def process(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        """Process a natural language prompt for script generation."""
        logger.debug("Processing prompt", prompt_length=len(prompt))

        # Clean and normalize prompt
        processed_prompt = self._clean_prompt(prompt)

        # Detect prompt type
        prompt_type = self._detect_prompt_type(processed_prompt)

        # Enhance with context
        if context:
            processed_prompt = self._enhance_with_context(processed_prompt, context)

        # Apply template if applicable
        if prompt_type in self.prompt_templates:
            processed_prompt = self.prompt_templates[prompt_type].format(
                prompt=processed_prompt
            )

        # Add safety instructions
        processed_prompt = self._add_safety_instructions(processed_prompt)

        logger.debug(
            "Prompt processed",
            original_length=len(prompt),
            processed_length=len(processed_prompt),
            prompt_type=prompt_type,
        )

        return processed_prompt

    def _clean_prompt(self, prompt: str) -> str:
        """Clean and normalize the prompt."""
        # Remove excessive whitespace
        cleaned = re.sub(r"\s+", " ", prompt.strip())

        # Remove potentially harmful characters
        cleaned = re.sub(r'[^\w\s.,!?;:()\[\]{}"\'`~@#$%^&*+=|\\/<>-]', "", cleaned)

        return cleaned

    def _detect_prompt_type(self, prompt: str) -> str:
        """Detect the type of prompt based on keywords."""
        prompt_lower = prompt.lower()

        # Data processing keywords
        data_keywords = [
            "process",
            "analyze",
            "parse",
            "transform",
            "convert",
            "csv",
            "json",
            "data",
        ]
        if any(keyword in prompt_lower for keyword in data_keywords):
            return "data_processing"

        # File operations keywords
        file_keywords = [
            "file",
            "read",
            "write",
            "create",
            "delete",
            "move",
            "copy",
            "directory",
            "folder",
        ]
        if any(keyword in prompt_lower for keyword in file_keywords):
            return "file_operations"

        # API integration keywords
        api_keywords = [
            "api",
            "http",
            "request",
            "endpoint",
            "rest",
            "graphql",
            "fetch",
            "post",
            "get",
        ]
        if any(keyword in prompt_lower for keyword in api_keywords):
            return "api_integration"

        # Web scraping keywords
        scraping_keywords = [
            "scrape",
            "crawl",
            "extract",
            "html",
            "website",
            "url",
            "parse",
        ]
        if any(keyword in prompt_lower for keyword in scraping_keywords):
            return "web_scraping"

        # Automation keywords
        automation_keywords = [
            "automate",
            "schedule",
            "batch",
            "loop",
            "repeat",
            "workflow",
        ]
        if any(keyword in prompt_lower for keyword in automation_keywords):
            return "automation"

        return "general"

    def _enhance_with_context(self, prompt: str, context: dict[str, Any]) -> str:
        """Enhance prompt with additional context."""
        enhanced_prompt = prompt

        # Add file context
        if "files" in context:
            file_list = ", ".join(context["files"])
            enhanced_prompt = f"Given files: {file_list}. {enhanced_prompt}"

        # Add data context (but not input values)
        if "data" in context:
            data_info = f"Data: {context['data']}"
            enhanced_prompt = f"{enhanced_prompt}\n\nContext: {data_info}"

        # Add environment context
        if "environment" in context:
            env_info = f"Environment: {context['environment']}"
            enhanced_prompt = f"{enhanced_prompt}\n\nEnvironment: {env_info}"

        # Handle inputs separately - don't include them in the prompt for caching
        # but add type information for function generation
        if "inputs" in context:
            inputs = context["inputs"]
            if isinstance(inputs, list) and len(inputs) > 0:
                # Determine input types and add to prompt for function signature
                input_types = []
                for input_val in inputs:
                    if isinstance(input_val, str):
                        # Try to determine if it's a number
                        try:
                            float(input_val)
                            input_types.append("number")
                        except ValueError:
                            input_types.append("string")
                    elif isinstance(input_val, (int, float)):
                        input_types.append("number")
                    elif isinstance(input_val, bool):
                        input_types.append("boolean")
                    else:
                        input_types.append("string")

                # Add input type information to prompt
                type_info = f"The function should accept {len(inputs)} parameters of types: {', '.join(set(input_types))}"
                enhanced_prompt = f"{enhanced_prompt}\n\n{type_info}"

        return enhanced_prompt

    def _add_safety_instructions(self, prompt: str) -> str:
        """Add safety instructions to the prompt."""
        safety_instructions = """

        IMPORTANT SAFETY REQUIREMENTS:
        - Generate safe, production-ready code
        - Include proper error handling
        - Use secure coding practices
        - Avoid dangerous operations (file system access, network calls, subprocess execution)
        - Include input validation where applicable
        - Add appropriate logging
        - Follow the specified programming language best practices
        """

        return f"{prompt}{safety_instructions}"

    def extract_requirements(self, prompt: str) -> list[str]:
        """Extract requirements from the prompt."""
        requirements = []

        # Look for specific requirements patterns
        requirement_patterns = [
            r"requirements?:\s*(.+)",
            r"needs?:\s*(.+)",
            r"must\s+(.+)",
            r"should\s+(.+)",
        ]

        for pattern in requirement_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            for match in matches:
                requirements.extend([req.strip() for req in match.split(",")])

        return requirements

    def extract_constraints(self, prompt: str) -> list[str]:
        """Extract constraints from the prompt."""
        constraints = []

        # Look for constraint patterns
        constraint_patterns = [
            r"constraints?:\s*(.+)",
            r"limitations?:\s*(.+)",
            r"cannot\s+(.+)",
            r"must not\s+(.+)",
        ]

        for pattern in constraint_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            for match in matches:
                constraints.extend(
                    [constraint.strip() for constraint in match.split(",")]
                )

        return constraints
