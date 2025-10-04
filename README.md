# Capibara Core

A secure, production-ready developer tool that generates executable scripts from natural language prompts using LLMs.

## Architecture

Capibara is built with a modular architecture featuring:
- **Core Engine**: Script generation and processing
- **LLM Provider Layer**: Multi-provider support with fallback
- **Security Layer**: Sandbox execution and AST scanning
- **SDK & CLI**: Developer-friendly interfaces
- **Container Runtime**: Safe script execution

## Quick Start

```bash
# Install
pip install -e .

# Run a script
capibara run "process this CSV file and generate a summary"

# List cached scripts
capibara list

# Show script details
capibara show <script_id>
```

## Security

- Containerized execution with no network access by default
- AST scanning to block dangerous patterns
- Resource limits (CPU, memory, time)
- Comprehensive audit logging
