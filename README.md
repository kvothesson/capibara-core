# Capibara Core

A secure, production-ready AI-powered script generation and execution platform.

## 🚀 Features

- **Multi-LLM Support**: OpenAI, Groq with automatic fallback
- **Secure Execution**: Docker containerized sandboxing
- **Content-Addressable Cache**: SHA-256 based caching
- **Security Scanning**: AST-based static analysis
- **Developer Experience**: Simple SDK and CLI
- **Production Ready**: Comprehensive logging, metrics, and monitoring

## 📦 Installation

### Option 1: Quick Install (Recommended)
```bash
# Clone and install
git clone https://github.com/kvothesson/capibara-core.git
cd capibara-core
./install.sh
```

### Option 2: Manual Install
```bash
# Install dependencies
pip install -e .

# Install Docker (if not installed)
# macOS: brew install --cask docker
# Linux: curl -fsSL https://get.docker.com | sh

# Configure API keys
cp env.example ~/.capibara/.env
nano ~/.capibara/.env  # Add your API keys
```

## 🎯 Quick Start

```bash
# Check system health
capibara doctor

# Generate and execute a script
capibara run "Create a hello world program" --execute

# List cached scripts
capibara list

# Show script details
capibara show <script_id>

# Clear cache
capibara clear --all
```

## 🐍 Python SDK

```python
from capibara import CapibaraClient

# Initialize client
client = CapibaraClient(
    groq_api_key="your_groq_key",
    openai_api_key="your_openai_key"
)

# Generate and execute script
response = await client.run(
    prompt="Create a data analysis script",
    language="python",
    execute=True
)

print(f"Script ID: {response.script_id}")
print(f"Code: {response.code}")
print(f"Execution Result: {response.execution_result}")
```

## 🏗️ Architecture

- `core/` - Core engine and script generation
- `llm_providers/` - LLM provider abstractions
- `runner/` - Container execution and resource management
- `security/` - Security scanning and policy enforcement
- `sdk/` - Python SDK and client
- `cli/` - Command-line interface
- `utils/` - Utilities and helpers

## 🔧 Configuration

Environment variables (set in `~/.capibara/.env`):

```bash
# Required: At least one LLM provider
GROQ_API_KEY=gsk_your_groq_api_key_here
OPENAI_API_KEY=sk-your_openai_api_key_here

# Optional: Default settings
DEFAULT_LANGUAGE=python
DEFAULT_SECURITY_POLICY=moderate
CACHE_TTL=3600
```

## 📚 Examples

See the `examples/` directory for:
- Basic usage (`hello_world.py`)
- Advanced data analysis (`data_analysis.py`)
- Security features (`safe_script.py`)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.