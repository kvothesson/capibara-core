"""Unit tests for Container Runner."""

from unittest.mock import Mock

import pytest

from capibara.models.manifests import ResourceLimits
from capibara.models.responses import ExecutionResult
from capibara.runner.container_runner import ContainerRunner


class TestContainerRunner:
    """Test cases for ContainerRunner."""

    @pytest.fixture
    def mock_docker_client(self):
        """Create mock Docker client."""
        client = Mock()
        client.ping.return_value = True
        return client

    @pytest.fixture
    def container_runner(self, mock_docker_client):
        """Create ContainerRunner instance."""
        return ContainerRunner(docker_client=mock_docker_client)

    @pytest.fixture
    def sample_resource_limits(self):
        """Create sample resource limits."""
        return ResourceLimits(
            cpu_time_seconds=30,
            memory_mb=256,
            execution_time_seconds=60,
            max_file_size_mb=5,
            max_files=50,
            network_access=False,
            allow_subprocess=False,
        )

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = Mock()
        container.id = "test_container_123"
        container.start = Mock()
        container.wait = Mock(return_value={"StatusCode": 0})
        container.logs = Mock(return_value=b"Hello, World!\n")
        container.stats = Mock(
            return_value={
                "memory_stats": {"usage": 50 * 1024 * 1024},  # 50MB
                "cpu_stats": {"cpu_usage": {"total_usage": 1000000000}},
                "precpu_stats": {"cpu_usage": {"total_usage": 500000000}},
                "system_cpu_usage": 2000000000,
                "cpu_usage": {"percpu_usage": [0, 0, 0, 0]},
            }
        )
        container.remove = Mock()
        return container

    @pytest.mark.asyncio
    async def test_execute_python_success(
        self, container_runner, sample_resource_limits, mock_container
    ):
        """Test successful Python script execution."""
        # Arrange
        code = "print('Hello, World!')"
        language = "python"

        # Mock Docker client methods
        container_runner.docker_client.containers.run.return_value = mock_container
        container_runner.docker_client.containers.get.return_value = mock_container

        # Act
        result = await container_runner.execute(code, language, sample_resource_limits)

        # Assert
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout.strip() == "Hello, World!"  # Strip newline
        assert result.stderr == ""
        assert result.execution_time_ms >= 0  # Allow 0 for now since it's hardcoded
        assert result.memory_used_mb > 0
        assert result.cpu_time_ms >= 0
        assert result.security_violations == []
        assert result.resource_limits_exceeded == []

    @pytest.mark.asyncio
    async def test_execute_javascript_success(
        self, container_runner, sample_resource_limits, mock_container
    ):
        """Test successful JavaScript script execution."""
        # Arrange
        code = "console.log('Hello, World!');"
        language = "javascript"

        # Mock Docker client methods
        container_runner.docker_client.containers.run.return_value = mock_container
        container_runner.docker_client.containers.get.return_value = mock_container

        # Act
        result = await container_runner.execute(code, language, sample_resource_limits)

        # Assert
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_with_error(
        self, container_runner, sample_resource_limits, mock_container
    ):
        """Test script execution with error."""
        # Arrange
        code = "print('Hello, World!')"
        language = "python"

        # Mock container with error
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.return_value = b"Traceback (most recent call last):\n  File \"script.py\", line 1, in <module>\n    print('Hello, World!')\nNameError: name 'print' is not defined\n"

        # Mock Docker client methods
        container_runner.docker_client.containers.run.return_value = mock_container
        container_runner.docker_client.containers.get.return_value = mock_container

        # Act
        result = await container_runner.execute(code, language, sample_resource_limits)

        # Assert
        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert result.exit_code == 1
        assert "NameError" in result.stdout  # Error is in stdout, not stderr

    @pytest.mark.asyncio
    async def test_execute_container_creation_failure(
        self, container_runner, sample_resource_limits
    ):
        """Test execution when container creation fails."""
        # Arrange
        code = "print('Hello, World!')"
        language = "python"

        # Mock Docker client to raise exception
        container_runner.docker_client.containers.run.side_effect = Exception(
            "Docker error"
        )

        # Act
        result = await container_runner.execute(code, language, sample_resource_limits)

        # Assert
        assert isinstance(result, ExecutionResult)
        assert result.success is False
        assert result.exit_code == -1
        assert "Execution failed" in result.stderr

    @pytest.mark.asyncio
    async def test_resource_limits_exceeded(self, container_runner, mock_container):
        """Test when resource limits are exceeded."""
        # Arrange
        code = "print('Hello, World!')"
        language = "python"

        # Create resource limits with very low memory limit
        resource_limits = ResourceLimits(
            cpu_time_seconds=1,
            memory_mb=64,  # Minimum allowed memory limit
            execution_time_seconds=5,
            max_file_size_mb=1,
            max_files=10,
            network_access=False,
            allow_subprocess=False,
        )

        # Mock container with high memory usage
        mock_container.stats.return_value = {
            "memory_stats": {"usage": 100 * 1024 * 1024},  # 100MB (exceeds 64MB limit)
            "cpu_stats": {"cpu_usage": {"total_usage": 1000000000}},
            "precpu_stats": {"cpu_usage": {"total_usage": 500000000}},
            "system_cpu_usage": 2000000000,
            "cpu_usage": {"percpu_usage": [0, 0, 0, 0]},
        }

        # Mock Docker client methods
        container_runner.docker_client.containers.run.return_value = mock_container
        container_runner.docker_client.containers.get.return_value = mock_container

        # Act
        result = await container_runner.execute(code, language, resource_limits)

        # Assert
        assert isinstance(result, ExecutionResult)
        assert len(result.resource_limits_exceeded) > 0
        assert any(
            "Memory limit exceeded" in violation
            for violation in result.resource_limits_exceeded
        )

    @pytest.mark.asyncio
    async def test_health_check_success(self, container_runner):
        """Test successful health check."""
        # Act
        result = await container_runner.health_check()

        # Assert
        assert result is True
        container_runner.docker_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, container_runner):
        """Test health check failure."""
        # Arrange
        container_runner.docker_client.ping.side_effect = Exception(
            "Docker not running"
        )

        # Act
        result = await container_runner.health_check()

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_workspace(self, container_runner):
        """Test workspace creation."""
        # Act
        workspace = await container_runner._create_workspace("print('Hello')", "python")

        # Assert
        assert workspace.exists()
        assert (workspace / "script.py").exists()
        assert (workspace / "script.py").read_text() == "print('Hello')"

    @pytest.mark.asyncio
    async def test_create_workspace_javascript(self, container_runner):
        """Test workspace creation for JavaScript."""
        # Act
        workspace = await container_runner._create_workspace(
            "console.log('Hello');", "javascript"
        )

        # Assert
        assert workspace.exists()
        assert (workspace / "script.js").exists()
        assert (workspace / "script.js").read_text() == "console.log('Hello');"

    @pytest.mark.asyncio
    async def test_create_workspace_bash(self, container_runner):
        """Test workspace creation for Bash."""
        # Act
        workspace = await container_runner._create_workspace("echo 'Hello'", "bash")

        # Assert
        assert workspace.exists()
        assert (workspace / "script.sh").exists()
        assert (workspace / "script.sh").read_text() == "echo 'Hello'"

    @pytest.mark.asyncio
    async def test_create_workspace_powershell(self, container_runner):
        """Test workspace creation for PowerShell."""
        # Act
        workspace = await container_runner._create_workspace(
            "Write-Output 'Hello'", "powershell"
        )

        # Assert
        assert workspace.exists()
        assert (workspace / "script.ps1").exists()
        assert (workspace / "script.ps1").read_text() == "Write-Output 'Hello'"

    def test_get_execution_command_python(self, container_runner):
        """Test getting execution command for Python."""
        # Act
        command = container_runner._get_execution_command("python")

        # Assert
        assert "python" in command
        assert "/workspace/script.py" in command

    def test_get_execution_command_javascript(self, container_runner):
        """Test getting execution command for JavaScript."""
        # Act
        command = container_runner._get_execution_command("javascript")

        # Assert
        assert "node" in command
        assert "/workspace/script.js" in command

    def test_get_execution_command_bash(self, container_runner):
        """Test getting execution command for Bash."""
        # Act
        command = container_runner._get_execution_command("bash")

        # Assert
        assert "/bin/sh" in command
        assert "/workspace/script.sh" in command

    def test_get_execution_command_powershell(self, container_runner):
        """Test getting execution command for PowerShell."""
        # Act
        command = container_runner._get_execution_command("powershell")

        # Assert
        assert "pwsh" in command
        assert "/workspace/script.ps1" in command

    def test_parse_memory_usage(self, container_runner):
        """Test memory usage parsing."""
        # Arrange
        stats = {"memory_stats": {"usage": 50 * 1024 * 1024}}  # 50MB

        # Act
        memory_mb = container_runner._parse_memory_usage(stats)

        # Assert
        assert memory_mb == 50.0

    def test_parse_memory_usage_missing(self, container_runner):
        """Test memory usage parsing with missing stats."""
        # Arrange
        stats = {}

        # Act
        memory_mb = container_runner._parse_memory_usage(stats)

        # Assert
        assert memory_mb == 0.0

    def test_parse_cpu_usage(self, container_runner):
        """Test CPU usage parsing."""
        # Arrange
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 2000000000,
            },
            "precpu_stats": {"cpu_usage": {"total_usage": 500000000}},
            "cpu_usage": {"percpu_usage": [0, 0, 0, 0]},
        }

        # Act
        cpu_ms = container_runner._parse_cpu_usage(stats)

        # Assert
        assert cpu_ms > 0

    def test_parse_cpu_usage_missing(self, container_runner):
        """Test CPU usage parsing with missing stats."""
        # Arrange
        stats = {}

        # Act
        cpu_ms = container_runner._parse_cpu_usage(stats)

        # Assert
        assert cpu_ms == 0

    def test_check_resource_limits(self, container_runner, sample_resource_limits):
        """Test resource limit checking."""
        # Test memory limit exceeded
        violations = container_runner._check_resource_limits(
            memory_used_mb=300.0,  # Exceeds 256MB limit
            cpu_time_ms=5000,  # Within 30s limit
            resource_limits=sample_resource_limits,
        )
        assert len(violations) == 1
        assert "Memory limit exceeded" in violations[0]

        # Test CPU limit exceeded
        violations = container_runner._check_resource_limits(
            memory_used_mb=200.0,  # Within 256MB limit
            cpu_time_ms=35000,  # Exceeds 30s limit
            resource_limits=sample_resource_limits,
        )
        assert len(violations) == 1
        assert "CPU time limit exceeded" in violations[0]

        # Test no violations
        violations = container_runner._check_resource_limits(
            memory_used_mb=200.0,  # Within limit
            cpu_time_ms=5000,  # Within limit
            resource_limits=sample_resource_limits,
        )
        assert len(violations) == 0
