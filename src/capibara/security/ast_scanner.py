"""AST-based security scanning for generated scripts."""

import ast
import re

from capibara.models.manifests import SecurityPolicy
from capibara.models.security import SecurityScanResult, SecurityViolation
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class ASTScanner:
    """Scans generated code for security violations using AST analysis."""

    def __init__(self) -> None:
        self.dangerous_imports = {
            "os",
            "subprocess",
            "sys",
            "shutil",
            "glob",
            "fnmatch",
            "socket",
            "urllib",
            "http",
            "requests",
            "urllib3",
            "pickle",
            "marshal",
            "shelve",
            "dbm",
            "ctypes",
            "cffi",
            "cProfile",
            "pstats",
            "multiprocessing",
            "threading",
            "concurrent",
            "importlib",
            "imp",
            "pkgutil",
            "eval",
            "exec",
            "compile",
            "__import__",
        }

        self.dangerous_functions = {
            "eval",
            "exec",
            "compile",
            "__import__",
            "open",
            "file",
            "input",
            "raw_input",
            "exit",
            "quit",
            "reload",
        }

        self.dangerous_patterns = [
            r"os\.system\s*\(",
            r"subprocess\.",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"compile\s*\(",
            r'open\s*\([^)]*[\'"]w[\'"]',
            r'file\s*\([^)]*[\'"]w[\'"]',
        ]

    async def scan(
        self, code: str, language: str, policy: SecurityPolicy | None = None
    ) -> SecurityScanResult:
        """Scan code for security violations."""
        logger.debug("Starting security scan", language=language, code_length=len(code))

        scan_id = f"scan_{hash(code)}_{len(code)}"
        violations = []

        try:
            if language.lower() == "python":
                violations = await self._scan_python(code, policy)
            elif language.lower() == "javascript":
                violations = await self._scan_javascript(code, policy)
            elif language.lower() in ["bash", "sh"]:
                violations = await self._scan_bash(code, policy)
            elif language.lower() == "powershell":
                violations = await self._scan_powershell(code, policy)
            else:
                logger.warning(
                    "Unsupported language for AST scanning", language=language
                )
                violations = await self._scan_generic(code, policy)

            # Check for blocking violations
            blocking_violations = [v for v in violations if v.severity == "error"]
            passed = len(blocking_violations) == 0

            scan_result = SecurityScanResult(
                scan_id=scan_id,
                script_id="",  # Will be set by caller
                violations=violations,
                passed=passed,
                scan_duration_ms=0,  # Will be calculated
                rules_applied=self._get_applied_rules(policy),
            )

            logger.info(
                "Security scan completed",
                violations=len(violations),
                passed=passed,
                blocking_violations=len(blocking_violations),
            )

            return scan_result

        except Exception as e:
            logger.error("Security scan failed", error=str(e))
            # Return a failed scan result
            return SecurityScanResult(
                scan_id=scan_id,
                script_id="",
                violations=[
                    SecurityViolation(
                        violation_id=f"scan_error_{scan_id}",
                        rule_name="scan_error",
                        severity="error",
                        message=f"Security scan failed: {str(e)}",
                        pattern_matched="",
                    )
                ],
                passed=False,
                scan_duration_ms=0,
                rules_applied=[],
            )

    async def _scan_python(
        self, code: str, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan Python code for security violations."""
        violations = []

        try:
            # Parse AST
            tree = ast.parse(code)

            # Scan for dangerous imports
            violations.extend(self._scan_imports(tree, policy))

            # Scan for dangerous function calls
            violations.extend(self._scan_function_calls(tree, policy))

            # Scan for dangerous patterns
            violations.extend(self._scan_patterns(code, policy))

            # Apply custom policy rules
            if policy:
                violations.extend(self._apply_policy_rules(code, policy))

        except SyntaxError as e:
            violations.append(
                SecurityViolation(
                    violation_id=f"syntax_error_{hash(code)}",
                    rule_name="syntax_error",
                    severity="error",
                    message=f"Python syntax error: {str(e)}",
                    pattern_matched="",
                    line_number=getattr(e, "lineno", None),
                )
            )

        return violations

    async def _scan_javascript(
        self, code: str, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan JavaScript code for security violations."""
        violations = []

        # JavaScript-specific dangerous patterns
        js_patterns = [
            r"eval\s*\(",
            r"Function\s*\(",
            r"setTimeout\s*\([^,]*,\s*[^)]*\)",
            r"setInterval\s*\([^,]*,\s*[^)]*\)",
            r"document\.write\s*\(",
            r"innerHTML\s*=",
            r"outerHTML\s*=",
            r"document\.createElement\s*\(",
            r"XMLHttpRequest",
            r"fetch\s*\(",
        ]

        for pattern in js_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(
                    SecurityViolation(
                        violation_id=f"js_pattern_{hash(match.group())}",
                        rule_name="dangerous_pattern",
                        severity="error",
                        message=f"Dangerous JavaScript pattern detected: {match.group()}",
                        pattern_matched=match.group(),
                        line_number=code[: match.start()].count("\n") + 1,
                    )
                )

        # Apply generic pattern scanning
        violations.extend(await self._scan_generic(code, policy))

        return violations

    async def _scan_bash(
        self, code: str, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan Bash code for security violations."""
        violations = []

        # Bash-specific dangerous patterns
        bash_patterns = [
            r"rm\s+-rf",
            r"mkdir\s+/",
            r"chmod\s+777",
            r"wget\s+",
            r"curl\s+",
            r"nc\s+",
            r"netcat\s+",
            r"ssh\s+",
            r"scp\s+",
            r"rsync\s+",
            r">&\s*/dev/null",
            r"2>&1",
        ]

        for pattern in bash_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(
                    SecurityViolation(
                        violation_id=f"bash_pattern_{hash(match.group())}",
                        rule_name="dangerous_pattern",
                        severity="error",
                        message=f"Dangerous Bash pattern detected: {match.group()}",
                        pattern_matched=match.group(),
                        line_number=code[: match.start()].count("\n") + 1,
                    )
                )

        return violations

    async def _scan_powershell(
        self, code: str, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan PowerShell code for security violations."""
        violations = []

        # PowerShell-specific dangerous patterns
        ps_patterns = [
            r"Invoke-Expression",
            r"Invoke-Command",
            r"Start-Process",
            r"Remove-Item\s+-Recurse",
            r"Set-ExecutionPolicy",
            r"Get-Content\s+.*\.exe",
            r"Invoke-WebRequest",
            r"Invoke-RestMethod",
        ]

        for pattern in ps_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(
                    SecurityViolation(
                        violation_id=f"ps_pattern_{hash(match.group())}",
                        rule_name="dangerous_pattern",
                        severity="error",
                        message=f"Dangerous PowerShell pattern detected: {match.group()}",
                        pattern_matched=match.group(),
                        line_number=code[: match.start()].count("\n") + 1,
                    )
                )

        return violations

    async def _scan_generic(
        self, code: str, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Generic pattern-based scanning for any language."""
        violations = []

        # Scan for dangerous patterns
        for pattern in self.dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(
                    SecurityViolation(
                        violation_id=f"generic_pattern_{hash(match.group())}",
                        rule_name="dangerous_pattern",
                        severity="error",
                        message=f"Dangerous pattern detected: {match.group()}",
                        pattern_matched=match.group(),
                        line_number=code[: match.start()].count("\n") + 1,
                    )
                )

        return violations

    def _scan_imports(
        self, tree: ast.AST, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan for dangerous imports in Python AST."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name = self._get_module_name(node)

                if module_name in self.dangerous_imports:
                    # Check if this import is allowed by policy
                    if policy and self._is_import_allowed(module_name, policy):
                        continue

                    violations.append(
                        SecurityViolation(
                            violation_id=f"import_{module_name}_{hash(str(node))}",
                            rule_name="dangerous_import",
                            severity="error",
                            message=f"Dangerous import detected: {module_name}",
                            pattern_matched=module_name,
                            line_number=getattr(node, "lineno", None),
                            code_snippet=ast.unparse(node),
                        )
                    )

        return violations

    def _scan_function_calls(
        self, tree: ast.AST, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan for dangerous function calls in Python AST."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)

                if func_name in self.dangerous_functions:
                    # Check if this function is allowed by policy
                    if policy and self._is_function_allowed(func_name, policy):
                        continue

                    violations.append(
                        SecurityViolation(
                            violation_id=f"function_{func_name}_{hash(str(node))}",
                            rule_name="dangerous_function",
                            severity="error",
                            message=f"Dangerous function call detected: {func_name}",
                            pattern_matched=func_name,
                            line_number=getattr(node, "lineno", None),
                            code_snippet=ast.unparse(node),
                        )
                    )

        return violations

    def _scan_patterns(
        self, code: str, policy: SecurityPolicy | None
    ) -> list[SecurityViolation]:
        """Scan for dangerous patterns using regex."""
        violations = []

        for pattern in self.dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(
                    SecurityViolation(
                        violation_id=f"pattern_{hash(match.group())}",
                        rule_name="dangerous_pattern",
                        severity="error",
                        message=f"Dangerous pattern detected: {match.group()}",
                        pattern_matched=match.group(),
                        line_number=code[: match.start()].count("\n") + 1,
                    )
                )

        return violations

    def _apply_policy_rules(
        self, code: str, policy: SecurityPolicy
    ) -> list[SecurityViolation]:
        """Apply custom policy rules."""
        violations = []

        for rule in policy.rules:
            matches = re.finditer(rule.pattern, code, re.IGNORECASE)
            for match in matches:
                violations.append(
                    SecurityViolation(
                        violation_id=f"policy_{rule.name}_{hash(match.group())}",
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Policy violation: {rule.description}",
                        pattern_matched=match.group(),
                        line_number=code[: match.start()].count("\n") + 1,
                    )
                )

        return violations

    def _get_module_name(self, node: ast.AST) -> str:
        """Extract module name from import node."""
        if isinstance(node, ast.Import):
            return node.names[0].name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            return node.module or ""
        return ""

    def _get_function_name(self, node: ast.Call) -> str:
        """Extract function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _is_import_allowed(self, module_name: str, policy: SecurityPolicy) -> bool:
        """Check if import is allowed by policy."""
        # Check allowed imports
        for pattern in policy.allowed_imports:
            if re.match(pattern, module_name):
                return True

        # Check blocked imports
        for pattern in policy.blocked_imports:
            if re.match(pattern, module_name):
                return False

        return True

    def _is_function_allowed(self, func_name: str, policy: SecurityPolicy) -> bool:
        """Check if function is allowed by policy."""
        # Check allowed functions
        for pattern in policy.allowed_functions:
            if re.match(pattern, func_name):
                return True

        # Check blocked functions
        for pattern in policy.blocked_functions:
            if re.match(pattern, func_name):
                return False

        return True

    def _get_applied_rules(self, policy: SecurityPolicy | None) -> list[str]:
        """Get list of applied security rules."""
        rules = ["dangerous_import", "dangerous_function", "dangerous_pattern"]

        if policy:
            rules.extend([rule.name for rule in policy.rules])

        return rules
