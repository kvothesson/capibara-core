"""Unit tests for Capibara Engine."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from capibara.core.engine import CapibaraEngine, SecurityError
from capibara.models.requests import RunRequest
from capibara.models.security import SecurityScanResult, SecurityViolation


class TestCapibaraEngine:
    """Test cases for CapibaraEngine."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        cache_manager = Mock()
        script_generator = Mock()
        ast_scanner = Mock()
        policy_manager = Mock()
        container_runner = Mock()
        fallback_manager = Mock()

        return {
            "cache_manager": cache_manager,
            "script_generator": script_generator,
            "ast_scanner": ast_scanner,
            "policy_manager": policy_manager,
            "container_runner": container_runner,
            "fallback_manager": fallback_manager,
        }

    @pytest.fixture
    def engine(self, mock_components):
        """Create engine instance with mocked components."""
        return CapibaraEngine(**mock_components)

    @pytest.fixture
    def sample_request(self):
        """Create sample run request."""
        return RunRequest(
            prompt="print('Hello, World!')",
            language="python",
            execute=False,
            security_policy="moderate",
            llm_provider="openai",
        )

    @pytest.fixture
    def sample_security_policy(self):
        """Create sample security policy."""
        policy = Mock()
        policy.resource_limits = Mock()
        policy.resource_limits.cpu_time_seconds = 30
        policy.resource_limits.memory_mb = 256
        return policy

    @pytest.mark.asyncio
    async def test_run_script_cache_hit(self, engine, sample_request, mock_components):
        """Test script generation with cache hit."""
        # Arrange
        cached_script = {
            "script_id": "test_script_123",
            "prompt": sample_request.prompt,
            "language": sample_request.language,
            "code": "print('Hello, World!')",
            "fingerprint": "test_fingerprint",
            "security_policy": sample_request.security_policy,
            "llm_provider": "openai",
            "created_at": datetime.now(UTC),
            "cache_hit_count": 0,
            "metadata": {},
        }

        mock_components["cache_manager"].get_script = AsyncMock(
            return_value=cached_script
        )
        mock_components["cache_manager"].increment_cache_hit = AsyncMock()

        # Act
        response = await engine.run_script(sample_request)

        # Assert
        assert response.cached is True
        assert response.script_id == "test_script_123"
        assert response.code == "print('Hello, World!')"
        mock_components["cache_manager"].get_script.assert_called_once()
        mock_components["cache_manager"].increment_cache_hit.assert_called_once_with(
            "test_script_123"
        )

    @pytest.mark.asyncio
    async def test_run_script_cache_miss_generation(
        self, engine, sample_request, mock_components, sample_security_policy
    ):
        """Test script generation with cache miss."""
        # Arrange
        mock_components["cache_manager"].get_script = AsyncMock(return_value=None)
        engine.prompt_processor.process = AsyncMock(return_value="processed_prompt")
        mock_components["script_generator"].generate = AsyncMock(
            return_value="print('Hello, World!')"
        )
        mock_components["script_generator"].last_provider_used = "openai"
        mock_components["policy_manager"].get_policy.return_value = (
            sample_security_policy
        )

        # Mock successful security scan
        scan_result = SecurityScanResult(
            scan_id="test_scan",
            script_id="",
            violations=[],
            passed=True,
            scan_duration_ms=10,
            rules_applied=["test_rule"],
        )
        mock_components["ast_scanner"].scan = AsyncMock(return_value=scan_result)
        mock_components["cache_manager"].store_script = AsyncMock()

        # Act
        response = await engine.run_script(sample_request)

        # Assert
        assert response.cached is False
        assert response.code == "print('Hello, World!')"
        assert response.llm_provider == "openai"

        engine.prompt_processor.process.assert_called_once()
        mock_components["script_generator"].generate.assert_called_once()
        mock_components["ast_scanner"].scan.assert_called_once()
        mock_components["cache_manager"].store_script.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_script_security_scan_failure(
        self, engine, sample_request, mock_components, sample_security_policy
    ):
        """Test script generation with security scan failure."""
        # Arrange
        mock_components["cache_manager"].get_script = AsyncMock(return_value=None)
        engine.prompt_processor.process = AsyncMock(return_value="processed_prompt")
        mock_components["script_generator"].generate = AsyncMock(
            return_value="import os; os.system('rm -rf /')"
        )
        mock_components["policy_manager"].get_policy.return_value = (
            sample_security_policy
        )

        # Mock failed security scan
        violation = SecurityViolation(
            violation_id="test_violation",
            rule_name="dangerous_import",
            severity="error",
            message="Dangerous import detected: os",
            pattern_matched="import os",
        )
        scan_result = SecurityScanResult(
            scan_id="test_scan",
            script_id="",
            violations=[violation],
            passed=False,
            scan_duration_ms=10,
            rules_applied=["dangerous_import"],
        )
        mock_components["ast_scanner"].scan = AsyncMock(return_value=scan_result)

        # Act & Assert
        with pytest.raises(SecurityError) as exc_info:
            await engine.run_script(sample_request)

        assert len(exc_info.value.violations) == 1
        assert exc_info.value.violations[0].rule_name == "dangerous_import"

    @pytest.mark.asyncio
    async def test_run_script_with_execution(
        self, engine, sample_request, mock_components, sample_security_policy
    ):
        """Test script generation with execution."""
        # Arrange
        sample_request.execute = True
        mock_components["cache_manager"].get_script = AsyncMock(return_value=None)
        engine.prompt_processor.process = AsyncMock(return_value="processed_prompt")
        mock_components["script_generator"].generate = AsyncMock(
            return_value="print('Hello, World!')"
        )
        mock_components["script_generator"].last_provider_used = "openai"
        mock_components["policy_manager"].get_policy.return_value = (
            sample_security_policy
        )

        # Mock successful security scan
        scan_result = SecurityScanResult(
            scan_id="test_scan",
            script_id="",
            violations=[],
            passed=True,
            scan_duration_ms=10,
            rules_applied=["test_rule"],
        )
        mock_components["ast_scanner"].scan = AsyncMock(return_value=scan_result)
        mock_components["cache_manager"].store_script = AsyncMock()

        # Mock execution result
        from capibara.models.responses import ExecutionResult

        execution_result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="Hello, World!",
            stderr="",
            execution_time_ms=100,
            memory_used_mb=50.0,
        )

        mock_components["container_runner"].execute = AsyncMock(
            return_value=execution_result
        )

        # Act
        response = await engine.run_script(sample_request)

        # Assert
        assert response.execution_result is not None
        assert response.execution_result.success is True
        assert response.execution_result.stdout == "Hello, World!"

        mock_components["container_runner"].execute.assert_called_once()

    def test_generate_script_id(self, engine):
        """Test script ID generation."""
        script_id = engine._generate_script_id()

        assert script_id.startswith("script_")
        assert len(script_id) > 20  # Should have timestamp + hash

    def test_generate_event_id(self, engine):
        """Test event ID generation."""
        event_id = engine._generate_event_id()

        assert event_id.startswith("event_")
        assert len(event_id) > 20  # Should have timestamp + hash

    def test_modify_python_code_for_execution(self, engine, sample_request):
        """Test Python code modification for execution."""
        # Arrange
        sample_request.context = {"inputs": ["1.0", "2.0", "3.0"]}
        code = "def calculate(a, b, c):\n    return (1.0, 2.0, 3.0)"

        # Act
        modified_code = engine._modify_python_code(
            code, sample_request.context["inputs"]
        )

        # Assert
        assert "1.0" in modified_code
        assert "2.0" in modified_code
        assert "3.0" in modified_code
