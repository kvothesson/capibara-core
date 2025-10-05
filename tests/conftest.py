"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from unittest.mock import Mock
from datetime import datetime, timezone

from capibara.models.requests import RunRequest
from capibara.models.responses import RunResponse
from capibara.models.security import SecurityScanResult, SecurityViolation
from capibara.models.manifests import SecurityPolicy, SecurityRule, ResourceLimits


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_run_request():
    """Create a sample RunRequest for testing."""
    return RunRequest(
        prompt="print('Hello, World!')",
        language="python",
        execute=False,
        security_policy="moderate",
        llm_provider="openai",
        context={"test": "data"}
    )


@pytest.fixture
def sample_run_response():
    """Create a sample RunResponse for testing."""
    return RunResponse(
        script_id="test_script_123",
        prompt="print('Hello, World!')",
        language="python",
        code="print('Hello, World!')",
        execution_result=None,
        cached=False,
        security_policy="moderate",
        llm_provider="openai",
        fingerprint="test_fingerprint_123",
        created_at=datetime.now(timezone.utc),
        metadata={"test": "metadata"}
    )


@pytest.fixture
def sample_security_violation():
    """Create a sample SecurityViolation for testing."""
    return SecurityViolation(
        violation_id="test_violation_123",
        rule_name="dangerous_import",
        severity="error",
        message="Dangerous import detected: os",
        pattern_matched="import os",
        line_number=1,
        code_snippet="import os"
    )


@pytest.fixture
def sample_security_scan_result():
    """Create a sample SecurityScanResult for testing."""
    return SecurityScanResult(
        scan_id="test_scan_123",
        script_id="test_script_123",
        violations=[],
        passed=True,
        scan_duration_ms=10,
        rules_applied=["test_rule"]
    )


@pytest.fixture
def sample_security_policy():
    """Create a sample SecurityPolicy for testing."""
    return SecurityPolicy(
        name="test_policy",
        description="Test security policy",
        rules=[
            SecurityRule(
                name="test_rule",
                description="Test rule",
                pattern=r"test_pattern",
                severity="error",
                action="block"
            )
        ],
        blocked_imports=["dangerous_module"],
        blocked_functions=["dangerous_function"],
        allowed_imports=["safe_module"],
        allowed_functions=["safe_function"],
        resource_limits=ResourceLimits(
            cpu_time_seconds=30,
            memory_mb=256,
            execution_time_seconds=60,
            max_file_size_mb=5,
            max_files=50,
            network_access=False,
            allow_subprocess=False
        )
    )


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache_manager = Mock()
    cache_manager.get_script = Mock(return_value=None)
    cache_manager.store_script = Mock()
    cache_manager.increment_cache_hit = Mock()
    cache_manager.list_scripts = Mock(return_value=[])
    cache_manager.clear_scripts = Mock(return_value=0)
    cache_manager.get_cache_stats = Mock(return_value={})
    return cache_manager


@pytest.fixture
def mock_script_generator():
    """Create a mock script generator."""
    generator = Mock()
    generator.generate = Mock(return_value="print('Hello, World!')")
    generator.last_provider_used = "openai"
    generator.get_generation_stats = Mock(return_value={})
    return generator


@pytest.fixture
def mock_ast_scanner():
    """Create a mock AST scanner."""
    scanner = Mock()
    scanner.scan = Mock(return_value=SecurityScanResult(
        scan_id="test_scan",
        script_id="",
        violations=[],
        passed=True,
        scan_duration_ms=10,
        rules_applied=["test_rule"]
    ))
    return scanner


@pytest.fixture
def mock_policy_manager():
    """Create a mock policy manager."""
    manager = Mock()
    policy = SecurityPolicy(
        name="test_policy",
        description="Test policy",
        rules=[],
        blocked_imports=[],
        blocked_functions=[],
        allowed_imports=[],
        allowed_functions=[],
        resource_limits=ResourceLimits()
    )
    manager.get_policy = Mock(return_value=policy)
    return manager


@pytest.fixture
def mock_container_runner():
    """Create a mock container runner."""
    runner = Mock()
    runner.execute = Mock()
    runner.health_check = Mock(return_value=True)
    return runner


@pytest.fixture
def mock_fallback_manager():
    """Create a mock fallback manager."""
    manager = Mock()
    manager.get_provider_stats = Mock(return_value={})
    return manager
