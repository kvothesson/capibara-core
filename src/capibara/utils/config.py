"""Configuration management for Capibara Core."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv  # type: ignore[import-not-found]

from capibara.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "sqlite:///capibara.db"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False


@dataclass
class CacheConfig:
    """Cache configuration."""

    dir: str = "~/.capibara/cache"
    ttl: int = 3600  # seconds
    max_size_mb: int = 1024
    cleanup_interval: int = 300  # seconds


@dataclass
class SecurityConfig:
    """Security configuration."""

    default_policy: str = "moderate"
    policies_dir: str = "config/security-policies"
    audit_log_dir: str = "~/.capibara/logs/audit"
    enable_audit_logging: bool = True


@dataclass
class ContainerConfig:
    """Container execution configuration."""

    image: str = "python:3.11-slim"
    memory_limit_mb: int = 512
    cpu_limit: float = 1.0
    execution_timeout: int = 60
    network_access: bool = False
    allow_subprocess: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    file: str | None = None
    max_size_mb: int = 100
    backup_count: int = 5


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    default_provider: str = "openai"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class MetricsConfig:
    """Metrics configuration."""

    enabled: bool = True
    port: int = 8080
    path: str = "/metrics"
    prometheus_endpoint: str = "http://localhost:9090"


@dataclass
class CapibaraConfig:
    """Main Capibara configuration."""

    # Core settings
    debug: bool = False
    environment: str = "development"

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    container: ContainerConfig = field(default_factory=ContainerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)

    # Additional settings
    custom_settings: dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_file: str | None = None):
        self.config_file = config_file
        self.config: CapibaraConfig | None = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from various sources."""
        # Start with defaults
        self.config = CapibaraConfig()
        assert self.config is not None  # Help mypy understand config is not None

        # Load from environment variables
        self._load_from_env()

        # Load from config file if provided
        if self.config_file and Path(self.config_file).exists():
            self._load_from_file(self.config_file)

        # Load from default config file locations
        self._load_from_default_locations()

        # Validate configuration
        self._validate_config()

        logger.info("Configuration loaded successfully")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        assert self.config is not None  # Config should be initialized by now

        # Load .env file if it exists
        env_files = [".env", "~/.capibara/.env", "/etc/capibara/.env"]

        for env_file in env_files:
            env_path = Path(env_file).expanduser()
            if env_path.exists():
                load_dotenv(env_path)
                logger.debug(f"Loaded environment from {env_path}")
                break

        # Core settings
        self.config.debug = self._get_bool_env("CAPIBARA_DEBUG", self.config.debug)
        self.config.environment = self._get_env(
            "CAPIBARA_ENVIRONMENT", self.config.environment
        )

        # Database settings
        self.config.database.url = self._get_env(
            "DATABASE_URL", self.config.database.url
        )
        self.config.database.pool_size = self._get_int_env(
            "DATABASE_POOL_SIZE", self.config.database.pool_size
        )
        self.config.database.max_overflow = self._get_int_env(
            "DATABASE_MAX_OVERFLOW", self.config.database.max_overflow
        )
        self.config.database.echo = self._get_bool_env(
            "DATABASE_ECHO", self.config.database.echo
        )

        # Cache settings
        self.config.cache.dir = self._get_env("CACHE_DIR", self.config.cache.dir)
        self.config.cache.ttl = self._get_int_env("CACHE_TTL", self.config.cache.ttl)
        self.config.cache.max_size_mb = self._get_int_env(
            "CACHE_MAX_SIZE_MB", self.config.cache.max_size_mb
        )
        self.config.cache.cleanup_interval = self._get_int_env(
            "CACHE_CLEANUP_INTERVAL", self.config.cache.cleanup_interval
        )

        # Security settings
        self.config.security.default_policy = self._get_env(
            "DEFAULT_SECURITY_POLICY", self.config.security.default_policy
        )
        self.config.security.policies_dir = self._get_env(
            "SECURITY_POLICIES_DIR", self.config.security.policies_dir
        )
        self.config.security.audit_log_dir = self._get_env(
            "AUDIT_LOG_DIR", self.config.security.audit_log_dir
        )
        self.config.security.enable_audit_logging = self._get_bool_env(
            "ENABLE_AUDIT_LOGGING", self.config.security.enable_audit_logging
        )

        # Container settings
        self.config.container.image = self._get_env(
            "DOCKER_IMAGE", self.config.container.image
        )
        self.config.container.memory_limit_mb = self._get_int_env(
            "DOCKER_MEMORY_LIMIT_MB", self.config.container.memory_limit_mb
        )
        self.config.container.cpu_limit = self._get_float_env(
            "DOCKER_CPU_LIMIT", self.config.container.cpu_limit
        )
        self.config.container.execution_timeout = self._get_int_env(
            "EXECUTION_TIMEOUT", self.config.container.execution_timeout
        )
        self.config.container.network_access = self._get_bool_env(
            "NETWORK_ACCESS", self.config.container.network_access
        )
        self.config.container.allow_subprocess = self._get_bool_env(
            "ALLOW_SUBPROCESS", self.config.container.allow_subprocess
        )

        # Logging settings
        self.config.logging.level = self._get_env(
            "LOG_LEVEL", self.config.logging.level
        )
        self.config.logging.format = self._get_env(
            "LOG_FORMAT", self.config.logging.format
        )
        self.config.logging.file = self._get_env("LOG_FILE", self.config.logging.file)
        self.config.logging.max_size_mb = self._get_int_env(
            "LOG_MAX_SIZE_MB", self.config.logging.max_size_mb
        )
        self.config.logging.backup_count = self._get_int_env(
            "LOG_BACKUP_COUNT", self.config.logging.backup_count
        )

        # LLM settings
        self.config.llm.openai_api_key = self._get_env(
            "OPENAI_API_KEY", self.config.llm.openai_api_key
        )
        self.config.llm.groq_api_key = self._get_env(
            "GROQ_API_KEY", self.config.llm.groq_api_key
        )
        self.config.llm.default_provider = self._get_env(
            "DEFAULT_LLM_PROVIDER", self.config.llm.default_provider
        )
        self.config.llm.max_tokens = self._get_int_env(
            "LLM_MAX_TOKENS", self.config.llm.max_tokens
        )
        self.config.llm.temperature = self._get_float_env(
            "LLM_TEMPERATURE", self.config.llm.temperature
        )
        self.config.llm.timeout = self._get_int_env(
            "LLM_TIMEOUT", self.config.llm.timeout
        )
        self.config.llm.retry_attempts = self._get_int_env(
            "LLM_RETRY_ATTEMPTS", self.config.llm.retry_attempts
        )

        # Metrics settings
        self.config.metrics.enabled = self._get_bool_env(
            "METRICS_ENABLED", self.config.metrics.enabled
        )
        self.config.metrics.port = self._get_int_env(
            "METRICS_PORT", self.config.metrics.port
        )
        self.config.metrics.path = self._get_env(
            "METRICS_PATH", self.config.metrics.path
        )
        self.config.metrics.prometheus_endpoint = self._get_env(
            "PROMETHEUS_ENDPOINT", self.config.metrics.prometheus_endpoint
        )

    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_file) as f:
                config_data = yaml.safe_load(f)

            if config_data:
                self._merge_config(config_data)
                logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")

    def _load_from_default_locations(self) -> None:
        """Load configuration from default locations."""
        default_locations = [
            "capibara.yaml",
            "capibara.yml",
            "config/capibara.yaml",
            "config/capibara.yml",
            "~/.capibara/config.yaml",
            "~/.capibara/config.yml",
            "/etc/capibara/config.yaml",
            "/etc/capibara/config.yml",
        ]

        for location in default_locations:
            config_path = Path(location).expanduser()
            if config_path.exists():
                self._load_from_file(str(config_path))
                break

    def _merge_config(self, config_data: dict[str, Any]) -> None:
        """Merge configuration data into current config."""
        assert self.config is not None  # Config should be initialized by now

        # This is a simplified merge - in production you'd want more sophisticated merging
        if "database" in config_data:
            db_config = config_data["database"]
            for key, value in db_config.items():
                if hasattr(self.config.database, key):
                    setattr(self.config.database, key, value)

        if "cache" in config_data:
            cache_config = config_data["cache"]
            for key, value in cache_config.items():
                if hasattr(self.config.cache, key):
                    setattr(self.config.cache, key, value)

        if "security" in config_data:
            security_config = config_data["security"]
            for key, value in security_config.items():
                if hasattr(self.config.security, key):
                    setattr(self.config.security, key, value)

        if "container" in config_data:
            container_config = config_data["container"]
            for key, value in container_config.items():
                if hasattr(self.config.container, key):
                    setattr(self.config.container, key, value)

        if "logging" in config_data:
            logging_config = config_data["logging"]
            for key, value in logging_config.items():
                if hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)

        if "llm" in config_data:
            llm_config = config_data["llm"]
            for key, value in llm_config.items():
                if hasattr(self.config.llm, key):
                    setattr(self.config.llm, key, value)

        if "metrics" in config_data:
            metrics_config = config_data["metrics"]
            for key, value in metrics_config.items():
                if hasattr(self.config.metrics, key):
                    setattr(self.config.metrics, key, value)

        # Handle custom settings
        if "custom" in config_data:
            self.config.custom_settings.update(config_data["custom"])

    def _validate_config(self) -> None:
        """Validate configuration settings."""
        assert self.config is not None  # Config should be initialized by now

        # Validate required API keys
        if not self.config.llm.openai_api_key and not self.config.llm.groq_api_key:
            logger.warning("No LLM API keys configured. At least one is required.")

        # Validate cache directory
        cache_dir = Path(self.config.cache.dir).expanduser()
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created cache directory: {cache_dir}")

        # Validate security policies directory
        policies_dir = Path(self.config.security.policies_dir).expanduser()
        if not policies_dir.exists():
            policies_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created security policies directory: {policies_dir}")

        # Validate audit log directory
        audit_dir = Path(self.config.security.audit_log_dir).expanduser()
        if not audit_dir.exists():
            audit_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created audit log directory: {audit_dir}")

        # Validate numeric ranges
        if self.config.cache.ttl <= 0:
            logger.warning("Cache TTL must be positive, using default")
            self.config.cache.ttl = 3600

        if self.config.container.memory_limit_mb <= 0:
            logger.warning("Container memory limit must be positive, using default")
            self.config.container.memory_limit_mb = 512

        if self.config.container.execution_timeout <= 0:
            logger.warning("Execution timeout must be positive, using default")
            self.config.container.execution_timeout = 60

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.config.logging.level.upper() not in valid_log_levels:
            logger.warning(
                f"Invalid log level: {self.config.logging.level}, using INFO"
            )
            self.config.logging.level = "INFO"

    def _get_env(self, key: str, default: str | None = "") -> str:
        """Get environment variable as string."""
        if default is None:
            default = ""
        return os.getenv(key, default)

    def _get_int_env(self, key: str, default: int) -> int:
        """Get environment variable as integer."""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default

    def _get_float_env(self, key: str, default: float) -> float:
        """Get environment variable as float."""
        try:
            return float(os.getenv(key, default))
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value for {key}, using default: {default}")
            return default

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get environment variable as boolean."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_config(self) -> CapibaraConfig:
        """Get the current configuration."""
        if self.config is None:
            raise RuntimeError("Configuration not loaded")
        return self.config

    def reload_config(self) -> None:
        """Reload configuration from sources."""
        logger.info("Reloading configuration...")
        self._load_config()

    def save_config(self, output_file: str) -> None:
        """Save current configuration to file."""
        assert self.config is not None  # Config should be initialized by now

        try:
            config_dict = {
                "database": {
                    "url": self.config.database.url,
                    "pool_size": self.config.database.pool_size,
                    "max_overflow": self.config.database.max_overflow,
                    "echo": self.config.database.echo,
                },
                "cache": {
                    "dir": self.config.cache.dir,
                    "ttl": self.config.cache.ttl,
                    "max_size_mb": self.config.cache.max_size_mb,
                    "cleanup_interval": self.config.cache.cleanup_interval,
                },
                "security": {
                    "default_policy": self.config.security.default_policy,
                    "policies_dir": self.config.security.policies_dir,
                    "audit_log_dir": self.config.security.audit_log_dir,
                    "enable_audit_logging": self.config.security.enable_audit_logging,
                },
                "container": {
                    "image": self.config.container.image,
                    "memory_limit_mb": self.config.container.memory_limit_mb,
                    "cpu_limit": self.config.container.cpu_limit,
                    "execution_timeout": self.config.container.execution_timeout,
                    "network_access": self.config.container.network_access,
                    "allow_subprocess": self.config.container.allow_subprocess,
                },
                "logging": {
                    "level": self.config.logging.level,
                    "format": self.config.logging.format,
                    "file": self.config.logging.file,
                    "max_size_mb": self.config.logging.max_size_mb,
                    "backup_count": self.config.logging.backup_count,
                },
                "llm": {
                    "default_provider": self.config.llm.default_provider,
                    "max_tokens": self.config.llm.max_tokens,
                    "temperature": self.config.llm.temperature,
                    "timeout": self.config.llm.timeout,
                    "retry_attempts": self.config.llm.retry_attempts,
                },
                "metrics": {
                    "enabled": self.config.metrics.enabled,
                    "port": self.config.metrics.port,
                    "path": self.config.metrics.path,
                    "prometheus_endpoint": self.config.metrics.prometheus_endpoint,
                },
                "custom": self.config.custom_settings,
            }

            with open(output_file, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise


# Global config manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> CapibaraConfig:
    """Get the current configuration."""
    return get_config_manager().get_config()


def reload_config() -> None:
    """Reload configuration."""
    get_config_manager().reload_config()
