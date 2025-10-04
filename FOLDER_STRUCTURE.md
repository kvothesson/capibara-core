# Capibara Core - Folder Structure

```
capibara-core/
├── README.md
├── pyproject.toml
├── FOLDER_STRUCTURE.md
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── security.yml
│       └── release.yml
├── config/
│   ├── security-policies.yaml
│   ├── llm-providers.yaml
│   └── logging.yaml
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── api-reference.md
│   └── examples/
├── examples/
│   ├── basic/
│   │   ├── hello_world.py
│   │   ├── csv_processing.py
│   │   └── file_manipulation.py
│   ├── advanced/
│   │   ├── data_analysis.py
│   │   ├── web_scraping.py
│   │   └── api_integration.py
│   └── security/
│       ├── safe_script.py
│       └── policy_examples.yaml
├── scripts/
│   ├── setup/
│   │   ├── install.sh
│   │   └── configure.sh
│   └── deploy/
│       ├── docker-build.sh
│       └── k8s-deploy.sh
├── src/
│   └── capibara/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── prompt_processor.py
│       │   ├── script_generator.py
│       │   └── cache_manager.py
│       ├── llm_providers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── openai_provider.py
│       │   ├── groq_provider.py
│       │   └── fallback_manager.py
│       ├── security/
│       │   ├── __init__.py
│       │   ├── ast_scanner.py
│       │   ├── policy_manager.py
│       │   ├── sandbox_config.py
│       │   └── audit_logger.py
│       ├── runner/
│       │   ├── __init__.py
│       │   ├── container_runner.py
│       │   ├── resource_limits.py
│       │   └── execution_monitor.py
│       ├── sdk/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── exceptions.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── run.py
│       │   │   ├── list.py
│       │   │   ├── show.py
│       │   │   └── clear.py
│       │   └── utils.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   ├── metrics.py
│       │   ├── fingerprinting.py
│       │   └── validation.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── requests.py
│       │   ├── responses.py
│       │   ├── manifests.py
│       │   └── security.py
│       └── examples/
│           ├── __init__.py
│           ├── basic_usage.py
│           └── advanced_usage.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_core/
│   │   ├── test_llm_providers/
│   │   ├── test_security/
│   │   ├── test_runner/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   ├── test_llm_integration.py
│   │   └── test_container_integration.py
│   ├── e2e/
│   │   ├── test_cli_workflow.py
│   │   └── test_sdk_workflow.py
│   └── security/
│       ├── test_ast_scanner.py
│       ├── test_sandbox_isolation.py
│       └── test_policy_enforcement.py
├── .vscode/
│   ├── settings.json
│   └── launch.json
└── .gitignore
```

## Key Directories

### `src/capibara/`
- **`core/`**: Core engine components (prompt processing, script generation, caching)
- **`llm_providers/`**: LLM provider implementations and fallback management
- **`security/`**: Security scanning, policy management, and audit logging
- **`runner/`**: Container execution and resource management
- **`sdk/`**: Public SDK interface for external integration
- **`cli/`**: Command-line interface implementation
- **`utils/`**: Shared utilities (logging, metrics, validation)
- **`models/`**: Pydantic data models for all data structures

### `tests/`
- **`unit/`**: Unit tests for individual components
- **`integration/`**: Integration tests for component interactions
- **`e2e/`**: End-to-end tests for complete workflows
- **`security/`**: Security-focused test suites

### `config/`
- Configuration files for security policies, LLM providers, and logging

### `examples/`
- Example scripts demonstrating different use cases and security patterns
