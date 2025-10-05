"""Sandbox configuration for secure script execution."""

from typing import Any

from pydantic import BaseModel, Field

from capibara.models.manifests import ResourceLimits
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class SandboxConfig(BaseModel):
    """Configuration for sandboxed script execution."""

    # Container settings
    container_runtime: str = Field(
        "docker", description="Container runtime (docker, podman)"
    )
    base_image: str = Field("python:3.11-slim", description="Base container image")
    working_directory: str = Field(
        "/workspace", description="Working directory in container"
    )
    user: str = Field("nobody", description="User to run as in container")

    # Environment
    environment: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    volumes: list[str] = Field(default_factory=list, description="Volume mounts")

    # Security settings
    security_opt: list[str] = Field(
        default_factory=list, description="Security options"
    )
    cap_drop: list[str] = Field(
        default_factory=list, description="Capabilities to drop"
    )
    cap_add: list[str] = Field(default_factory=list, description="Capabilities to add")
    seccomp_profile: str | None = Field(None, description="Seccomp profile path")
    apparmor_profile: str | None = Field(None, description="AppArmor profile name")

    # Network settings
    network_mode: str = Field("none", description="Network mode")

    # Filesystem settings
    read_only: bool = Field(True, description="Whether filesystem is read-only")

    # Resource limits
    resource_limits: ResourceLimits = Field(
        default_factory=ResourceLimits, description="Resource limits"
    )

    # Additional configuration
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )


class SandboxConfigManager:
    """Manages sandbox configurations for different security levels."""

    def __init__(self) -> None:
        self.configs: dict[str, SandboxConfig] = {}
        self._load_default_configs()

    def get_config(self, security_level: str = "moderate") -> SandboxConfig:
        """Get sandbox configuration for a security level."""
        if security_level in self.configs:
            logger.debug("Using sandbox config", level=security_level)
            return self.configs[security_level]

        logger.warning("Unknown security level, using moderate", level=security_level)
        return self.configs.get("moderate", self._create_basic_config())

    def add_config(self, name: str, config: SandboxConfig) -> None:
        """Add a custom sandbox configuration."""
        self.configs[name] = config
        logger.info("Sandbox config added", name=name)

    def list_configs(self) -> list[str]:
        """List available sandbox configurations."""
        return list(self.configs.keys())

    def _load_default_configs(self) -> None:
        """Load default sandbox configurations."""
        # Strict configuration
        strict_config = SandboxConfig(
            container_runtime="docker",
            base_image="python:3.11-slim",
            working_directory="/workspace",
            user="nobody",
            environment={
                "PYTHONPATH": "/workspace",
                "PYTHONUNBUFFERED": "1",
            },
            volumes=[],
            security_opt=[
                "no-new-privileges:true",
                "seccomp:unconfined",  # Will be overridden by seccomp_profile
            ],
            cap_drop=["ALL"],
            cap_add=[],
            seccomp_profile="strict.json",
            apparmor_profile="capibara-strict",
            network_mode="none",
            read_only=True,
            resource_limits=ResourceLimits(
                cpu_time_seconds=10,
                memory_mb=128,
                execution_time_seconds=30,
                max_file_size_mb=1,
                max_files=10,
                network_access=False,
                allow_subprocess=False,
            ),
        )

        # Moderate configuration
        moderate_config = SandboxConfig(
            container_runtime="docker",
            base_image="python:3.11-slim",
            working_directory="/workspace",
            user="nobody",
            environment={
                "PYTHONPATH": "/workspace",
                "PYTHONUNBUFFERED": "1",
            },
            volumes=[],
            security_opt=[
                "no-new-privileges:true",
                "seccomp:unconfined",  # Will be overridden by seccomp_profile
            ],
            cap_drop=["ALL"],
            cap_add=[],
            seccomp_profile="moderate.json",
            apparmor_profile="capibara-moderate",
            network_mode="none",
            read_only=True,
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

        # Permissive configuration
        permissive_config = SandboxConfig(
            container_runtime="docker",
            base_image="python:3.11-slim",
            working_directory="/workspace",
            user="nobody",
            environment={
                "PYTHONPATH": "/workspace",
                "PYTHONUNBUFFERED": "1",
            },
            volumes=[],
            security_opt=[
                "no-new-privileges:true",
                "seccomp:unconfined",  # Will be overridden by seccomp_profile
            ],
            cap_drop=["ALL"],
            cap_add=[],
            seccomp_profile="permissive.json",
            apparmor_profile="capibara-permissive",
            network_mode="none",
            read_only=False,  # Allow writes for permissive mode
            resource_limits=ResourceLimits(
                cpu_time_seconds=60,
                memory_mb=512,
                execution_time_seconds=120,
                max_file_size_mb=10,
                max_files=100,
                network_access=False,
                allow_subprocess=False,
            ),
        )

        # Add configurations
        self.configs["strict"] = strict_config
        self.configs["moderate"] = moderate_config
        self.configs["permissive"] = permissive_config

        logger.info("Default sandbox configs loaded", count=len(self.configs))

    def _create_basic_config(self) -> SandboxConfig:
        """Create a basic sandbox configuration as fallback."""
        return SandboxConfig(
            container_runtime="docker",
            base_image="python:3.11-slim",
            working_directory="/workspace",
            user="nobody",
            environment={
                "PYTHONPATH": "/workspace",
                "PYTHONUNBUFFERED": "1",
            },
            volumes=[],
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
            cap_add=[],
            seccomp_profile=None,
            apparmor_profile=None,
            network_mode="none",
            read_only=True,
            resource_limits=ResourceLimits(
                cpu_time_seconds=5,
                memory_mb=64,
                execution_time_seconds=15,
                max_file_size_mb=1,
                max_files=5,
                network_access=False,
                allow_subprocess=False,
            ),
        )

    def create_docker_config(self, config: SandboxConfig) -> dict[str, Any]:
        """Create Docker configuration from sandbox config."""
        docker_config = {
            "image": config.base_image,
            "working_dir": config.working_directory,
            "user": config.user,
            "environment": config.environment,
            "volumes": config.volumes,
            "security_opt": config.security_opt,
            "cap_drop": config.cap_drop,
            "cap_add": config.cap_add,
            "network_mode": config.network_mode,
            "read_only": config.read_only,
            "mem_limit": f"{config.resource_limits.memory_mb}m",
            "memswap_limit": f"{config.resource_limits.memory_mb}m",
            "cpu_period": 100000,
            "cpu_quota": int(config.resource_limits.cpu_time_seconds * 100000),
        }

        # Add seccomp profile if specified
        if config.seccomp_profile:
            security_opts = docker_config["security_opt"]
            assert isinstance(security_opts, list)
            security_opts.append(f"seccomp={config.seccomp_profile}")

        # Add AppArmor profile if specified
        if config.apparmor_profile:
            security_opts = docker_config["security_opt"]
            assert isinstance(security_opts, list)
            security_opts.append(f"apparmor={config.apparmor_profile}")

        return docker_config

    def create_podman_config(self, config: SandboxConfig) -> dict[str, Any]:
        """Create Podman configuration from sandbox config."""
        podman_config = {
            "image": config.base_image,
            "working_dir": config.working_directory,
            "user": config.user,
            "env": config.environment,
            "volumes": config.volumes,
            "security_opt": config.security_opt,
            "cap_drop": config.cap_drop,
            "cap_add": config.cap_add,
            "network": config.network_mode,
            "read_only": config.read_only,
            "memory": config.resource_limits.memory_mb
            * 1024
            * 1024,  # Convert to bytes
            "cpus": config.resource_limits.cpu_time_seconds,
        }

        # Add seccomp profile if specified
        if config.seccomp_profile:
            security_opts = podman_config["security_opt"]
            assert isinstance(security_opts, list)
            security_opts.append(f"seccomp={config.seccomp_profile}")

        # Add AppArmor profile if specified
        if config.apparmor_profile:
            security_opts = podman_config["security_opt"]
            assert isinstance(security_opts, list)
            security_opts.append(f"apparmor={config.apparmor_profile}")

        return podman_config
