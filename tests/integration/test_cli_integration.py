"""Integration tests for CLI functionality."""

from datetime import UTC
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from capibara.cli.main import cli


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_client(self):
        """Create mock client for testing."""
        client = Mock()
        client.run = AsyncMock()
        client.list_scripts = AsyncMock()
        client.show_script = AsyncMock()
        client.clear_cache = AsyncMock()
        client.health_check = AsyncMock()
        client.get_stats = Mock()
        return client

    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert (
            "Generate executable scripts from natural language prompts" in result.output
        )

    def test_cli_run_help(self, cli_runner):
        """Test CLI run command help."""
        result = cli_runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Generate and optionally execute a script" in result.output

    def test_cli_list_help(self, cli_runner):
        """Test CLI list command help."""
        result = cli_runner.invoke(cli, ["list-scripts", "--help"])
        assert result.exit_code == 0
        assert "List cached scripts" in result.output

    def test_cli_show_help(self, cli_runner):
        """Test CLI show command help."""
        result = cli_runner.invoke(cli, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show details of a specific script" in result.output

    def test_cli_clear_help(self, cli_runner):
        """Test CLI clear command help."""
        result = cli_runner.invoke(cli, ["clear", "--help"])
        assert result.exit_code == 0
        assert "Clear cache or specific scripts" in result.output

    def test_cli_health_help(self, cli_runner):
        """Test CLI health command help."""
        result = cli_runner.invoke(cli, ["health", "--help"])
        assert result.exit_code == 0
        assert "Check health of all components" in result.output

    def test_cli_stats_help(self, cli_runner):
        """Test CLI stats command help."""
        result = cli_runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0
        assert "Show statistics for all components" in result.output

    def test_cli_doctor_help(self, cli_runner):
        """Test CLI doctor command help."""
        result = cli_runner.invoke(cli, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "Check system health and dependencies" in result.output

    @patch("capibara.cli.main._get_client")
    def test_cli_run_basic(self, mock_get_client, cli_runner, mock_client):
        """Test basic CLI run command."""
        # Arrange
        mock_get_client.return_value = mock_client
        mock_response = Mock()
        mock_response.script_id = "test_script_123"
        mock_response.code = "print('Hello, World!')"
        mock_response.cached = False
        mock_response.llm_provider = "openai"
        mock_response.execution_result = None
        mock_client.run.return_value = mock_response

        # Act
        result = cli_runner.invoke(cli, ["run", "Hello World"])

        # Assert
        assert result.exit_code == 0
        assert "test_script_123" in result.output
        assert "Hello, World!" in result.output

    @patch("capibara.cli.main._get_client")
    def test_cli_run_with_execute(self, mock_get_client, cli_runner, mock_client):
        """Test CLI run command with execution."""
        # Arrange
        mock_get_client.return_value = mock_client
        mock_response = Mock()
        mock_response.script_id = "test_script_123"
        mock_response.code = "print('Hello, World!')"
        mock_response.cached = False
        mock_response.llm_provider = "openai"

        # Mock execution result
        mock_execution = Mock()
        mock_execution.success = True
        mock_execution.exit_code = 0
        mock_execution.execution_time_ms = 100
        mock_execution.memory_used_mb = 50.0
        mock_execution.stdout = "Hello, World!"
        mock_execution.stderr = ""
        mock_response.execution_result = mock_execution

        mock_client.run.return_value = mock_response

        # Act
        result = cli_runner.invoke(cli, ["run", "Hello World", "--execute"])

        # Assert
        assert result.exit_code == 0
        assert "test_script_123" in result.output
        assert "Hello, World!" in result.output
        assert "Success: True" in result.output
        assert "Exit Code: 0" in result.output

    @patch("capibara.cli.main._get_client")
    def test_cli_list_scripts(self, mock_get_client, cli_runner, mock_client):
        """Test CLI list scripts command."""
        from datetime import datetime

        from capibara.models.responses import ListResponse, ScriptInfo

        # Arrange
        mock_get_client.return_value = mock_client
        mock_scripts = [
            ScriptInfo(
                script_id="script_1",
                prompt="test prompt 1",
                language="python",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                execution_count=5,
                cache_hit_count=10,
                llm_provider="openai",
                fingerprint="fp1",
                size_bytes=100,
            ),
            ScriptInfo(
                script_id="script_2",
                prompt="test prompt 2",
                language="javascript",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                execution_count=3,
                cache_hit_count=7,
                llm_provider="groq",
                fingerprint="fp2",
                size_bytes=150,
            ),
        ]
        mock_response = ListResponse(
            scripts=mock_scripts, total_count=2, limit=50, offset=0, has_more=False
        )
        mock_client.list_scripts.return_value = mock_response

        # Act
        result = cli_runner.invoke(cli, ["list-scripts"])

        # Assert
        assert result.exit_code == 0
        assert "script_1" in result.output
        assert "script_2" in result.output
        assert "python" in result.output
        assert "javascript" in result.output

    @patch("capibara.cli.main._get_client")
    def test_cli_show_script(self, mock_get_client, cli_runner, mock_client):
        """Test CLI show script command."""
        from datetime import datetime

        from capibara.models.responses import ScriptInfo, ShowResponse

        # Arrange
        mock_get_client.return_value = mock_client
        mock_script = ScriptInfo(
            script_id="test_script_123",
            prompt="test prompt",
            language="python",
            llm_provider="openai",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            execution_count=5,
            cache_hit_count=10,
            size_bytes=1000,
            security_policy="moderate",
            fingerprint="test_fp",
            metadata={},
        )
        mock_response = ShowResponse(
            script=mock_script, code="print('Hello, World!')", execution_logs=None
        )
        mock_client.show_script.return_value = mock_response

        # Act
        result = cli_runner.invoke(cli, ["show", "test_script_123"])

        # Assert
        assert result.exit_code == 0
        assert "test_script_123" in result.output
        assert "test prompt" in result.output
        assert "python" in result.output
        assert "openai" in result.output
        assert "Hello, World!" in result.output

    @patch("capibara.cli.main._get_client")
    def test_cli_health_check(self, mock_get_client, cli_runner, mock_client):
        """Test CLI health check command."""
        # Arrange
        mock_get_client.return_value = mock_client
        mock_health = {
            "overall": True,
            "components": {
                "cache": {"healthy": True, "stats": {}},
                "llm_providers": {"healthy": True, "stats": {}},
                "container_runner": {"healthy": True},
            },
        }
        mock_client.health_check.return_value = mock_health

        # Act
        result = cli_runner.invoke(cli, ["health"])

        # Assert
        assert result.exit_code == 0
        assert "Healthy" in result.output
        assert "cache" in result.output
        assert "llm_providers" in result.output
        assert "container_runner" in result.output

    @patch("capibara.cli.main._get_client")
    def test_cli_stats(self, mock_get_client, cli_runner, mock_client):
        """Test CLI stats command."""
        # Arrange
        mock_get_client.return_value = mock_client
        mock_stats = {
            "cache": {
                "hits": 100,
                "misses": 50,
                "hit_rate_percent": 66.7,
                "total_scripts": 10,
                "total_size_bytes": 10000,
            },
            "llm_providers": {
                "total_requests": 150,
                "success_rate": 95.0,
                "providers": {
                    "openai": {
                        "successes": 100,
                        "requests": 100,
                        "success_rate": 100.0,
                    },
                    "groq": {"successes": 42, "requests": 50, "success_rate": 84.0},
                },
            },
            "script_generator": {
                "total_generations": 150,
                "success_rate_percent": 95.0,
            },
        }
        mock_client.get_stats.return_value = mock_stats

        # Act
        result = cli_runner.invoke(cli, ["stats"])

        # Assert
        assert result.exit_code == 0
        assert "100" in result.output  # cache hits
        assert "66.7" in result.output  # hit rate
        assert "150" in result.output  # total requests
        assert "95.0" in result.output  # success rate
        assert "openai" in result.output
        assert "groq" in result.output
