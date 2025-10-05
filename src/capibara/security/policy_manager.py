"""Security policy management for Capibara Core."""

from pathlib import Path

import yaml

from capibara.models.manifests import ResourceLimits, SecurityPolicy, SecurityRule
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class PolicyManager:
    """Manages security policies and their application."""

    def __init__(self, policies_dir: str = "config/security-policies"):
        self.policies_dir = Path(policies_dir)
        self.policies: dict[str, SecurityPolicy] = {}
        self.default_policy: SecurityPolicy | None = None

        # Load built-in policies
        self._load_builtin_policies()

        # Load custom policies
        self._load_custom_policies()

    def get_policy(self, policy_name: str | None = None) -> SecurityPolicy:
        """Get a security policy by name."""
        if policy_name and policy_name in self.policies:
            logger.debug("Using policy", policy=policy_name)
            return self.policies[policy_name]

        if self.default_policy:
            logger.debug("Using default policy")
            return self.default_policy

        # Return a basic restrictive policy if no policies are loaded
        logger.warning("No policies loaded, using basic restrictive policy")
        return self._create_basic_policy()

    def add_policy(self, policy: SecurityPolicy) -> None:
        """Add a new security policy."""
        self.policies[policy.name] = policy
        logger.info("Policy added", policy=policy.name)

    def remove_policy(self, policy_name: str) -> None:
        """Remove a security policy."""
        if policy_name in self.policies:
            del self.policies[policy_name]
            logger.info("Policy removed", policy=policy_name)

    def list_policies(self) -> list[str]:
        """List available policy names."""
        return list(self.policies.keys())

    def set_default_policy(self, policy_name: str) -> None:
        """Set the default policy."""
        if policy_name in self.policies:
            self.default_policy = self.policies[policy_name]
            logger.info("Default policy set", policy=policy_name)
        else:
            raise ValueError(f"Policy not found: {policy_name}")

    def _load_builtin_policies(self) -> None:
        """Load built-in security policies."""
        # Strict policy
        strict_policy = SecurityPolicy(
            name="strict",
            description="Strict security policy with maximum restrictions",
            rules=[
                SecurityRule(
                    name="no_dangerous_imports",
                    description="Block dangerous imports",
                    pattern=r"import\s+(os|subprocess|sys|shutil|socket|urllib|requests|pickle|ctypes|multiprocessing|threading|eval|exec|compile|__import__)",
                    severity="error",
                    action="block",
                ),
                SecurityRule(
                    name="no_dangerous_functions",
                    description="Block dangerous function calls",
                    pattern=r"(eval|exec|compile|__import__|open|file|input|exit|quit)\s*\(",
                    severity="error",
                    action="block",
                ),
                SecurityRule(
                    name="no_system_calls",
                    description="Block system calls",
                    pattern=r"os\.system|subprocess\.|os\.popen",
                    severity="error",
                    action="block",
                ),
            ],
            resource_limits=ResourceLimits(
                cpu_time_seconds=10,
                memory_mb=128,
                execution_time_seconds=30,
                max_file_size_mb=1,
                max_files=10,
                network_access=False,
                allow_subprocess=False,
            ),
            blocked_imports=[
                "os",
                "subprocess",
                "sys",
                "shutil",
                "socket",
                "urllib",
                "requests",
                "pickle",
                "ctypes",
                "multiprocessing",
                "threading",
                "eval",
                "exec",
                "compile",
                "__import__",
            ],
            blocked_functions=[
                "eval",
                "exec",
                "compile",
                "__import__",
                "open",
                "file",
                "input",
                "exit",
                "quit",
                "reload",
            ],
        )

        # Moderate policy
        moderate_policy = SecurityPolicy(
            name="moderate",
            description="Moderate security policy with balanced restrictions",
            rules=[
                SecurityRule(
                    name="no_dangerous_imports",
                    description="Block most dangerous imports",
                    pattern=r"import\s+(subprocess|socket|urllib|requests|pickle|ctypes|multiprocessing|threading|eval|exec|compile|__import__)",
                    severity="error",
                    action="block",
                ),
                SecurityRule(
                    name="no_dangerous_functions",
                    description="Block dangerous function calls",
                    pattern=r"(eval|exec|compile|__import__|exit|quit)\s*\(",
                    severity="error",
                    action="block",
                ),
                SecurityRule(
                    name="warn_system_calls",
                    description="Warn about system calls",
                    pattern=r"os\.system|subprocess\.",
                    severity="warning",
                    action="warn",
                ),
            ],
            resource_limits=ResourceLimits(
                cpu_time_seconds=30,
                memory_mb=256,
                execution_time_seconds=60,
                max_file_size_mb=5,
                max_files=50,
                network_access=False,
                allow_subprocess=False,
            ),
            blocked_imports=[
                "subprocess",
                "socket",
                "urllib",
                "requests",
                "pickle",
                "ctypes",
                "multiprocessing",
                "threading",
                "eval",
                "exec",
                "compile",
                "__import__",
            ],
            blocked_functions=[
                "eval",
                "exec",
                "compile",
                "__import__",
                "exit",
                "quit",
                "reload",
            ],
        )

        # Permissive policy
        permissive_policy = SecurityPolicy(
            name="permissive",
            description="Permissive security policy with minimal restrictions",
            rules=[
                SecurityRule(
                    name="no_eval_exec",
                    description="Block eval and exec",
                    pattern=r"(eval|exec|compile|__import__)\s*\(",
                    severity="error",
                    action="block",
                ),
                SecurityRule(
                    name="warn_dangerous_imports",
                    description="Warn about dangerous imports",
                    pattern=r"import\s+(subprocess|socket|urllib|requests|pickle|ctypes)",
                    severity="warning",
                    action="warn",
                ),
            ],
            resource_limits=ResourceLimits(
                cpu_time_seconds=60,
                memory_mb=512,
                execution_time_seconds=120,
                max_file_size_mb=10,
                max_files=100,
                network_access=False,
                allow_subprocess=False,
            ),
            blocked_imports=["eval", "exec", "compile", "__import__"],
            blocked_functions=["eval", "exec", "compile", "__import__"],
        )

        # Add built-in policies
        self.policies["strict"] = strict_policy
        self.policies["moderate"] = moderate_policy
        self.policies["permissive"] = permissive_policy

        # Set moderate as default
        self.default_policy = moderate_policy

        logger.info("Built-in policies loaded", count=len(self.policies))

    def _load_custom_policies(self) -> None:
        """Load custom security policies from files."""
        if not self.policies_dir.exists():
            logger.debug(
                "Policies directory does not exist", dir=str(self.policies_dir)
            )
            return

        policy_files = list(self.policies_dir.glob("*.yaml")) + list(
            self.policies_dir.glob("*.yml")
        )

        for policy_file in policy_files:
            try:
                with open(policy_file) as f:
                    policy_data = yaml.safe_load(f)

                policy = SecurityPolicy(**policy_data)
                self.policies[policy.name] = policy
                logger.info(
                    "Custom policy loaded", policy=policy.name, file=str(policy_file)
                )

            except Exception as e:
                logger.error(
                    "Failed to load custom policy", file=str(policy_file), error=str(e)
                )

    def _create_basic_policy(self) -> SecurityPolicy:
        """Create a basic restrictive policy as fallback."""
        return SecurityPolicy(
            name="basic",
            description="Basic restrictive policy",
            rules=[
                SecurityRule(
                    name="no_dangerous_imports",
                    description="Block all dangerous imports",
                    pattern=r"import\s+(os|subprocess|sys|shutil|socket|urllib|requests|pickle|ctypes|multiprocessing|threading|eval|exec|compile|__import__)",
                    severity="error",
                    action="block",
                ),
                SecurityRule(
                    name="no_dangerous_functions",
                    description="Block all dangerous functions",
                    pattern=r"(eval|exec|compile|__import__|open|file|input|exit|quit|reload)\s*\(",
                    severity="error",
                    action="block",
                ),
            ],
            resource_limits=ResourceLimits(
                cpu_time_seconds=5,
                memory_mb=64,
                execution_time_seconds=15,
                max_file_size_mb=1,
                max_files=5,
                network_access=False,
                allow_subprocess=False,
            ),
            blocked_imports=[
                "os",
                "subprocess",
                "sys",
                "shutil",
                "socket",
                "urllib",
                "requests",
                "pickle",
                "ctypes",
                "multiprocessing",
                "threading",
                "eval",
                "exec",
                "compile",
                "__import__",
            ],
            blocked_functions=[
                "eval",
                "exec",
                "compile",
                "__import__",
                "open",
                "file",
                "input",
                "exit",
                "quit",
                "reload",
            ],
        )

    def save_policy(self, policy: SecurityPolicy, filename: str | None = None) -> None:
        """Save a policy to a YAML file."""
        if not filename:
            filename = f"{policy.name}.yaml"

        policy_file = self.policies_dir / filename

        # Ensure directory exists
        policy_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(policy_file, "w") as f:
                yaml.dump(policy.dict(), f, default_flow_style=False, indent=2)

            logger.info("Policy saved", policy=policy.name, file=str(policy_file))

        except Exception as e:
            logger.error(
                "Failed to save policy",
                policy=policy.name,
                file=str(policy_file),
                error=str(e),
            )
            raise
