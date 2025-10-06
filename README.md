# Capibara Core

A secure, production-ready AI-powered script generation and execution platform.

## 🚀 Features

- **Multi-LLM Support**: OpenAI, Groq with automatic fallback
- **Secure Execution**: Docker containerized sandboxing
- **Content-Addressable Cache**: SHA-256 based caching
- **Security Scanning**: AST-based static analysis
- **Developer Experience**: Simple SDK and CLI
- **Production Ready**: Comprehensive logging, metrics, and monitoring

## 💡 Why Capibara?

**Stop writing boilerplate code for common tasks.** Capibara turns natural language into working, secure scripts that execute instantly.

| Task | Traditional Way | With Capibara |
|------|----------------|---------------|
| **Data Analysis** | Write pandas code, debug, test | `capibara run "analyze this CSV"` |
| **File Processing** | Write file handling, error checking | `capibara run "resize all images"` |
| **API Integration** | Write requests, handle errors, parse JSON | `capibara run "fetch from API"` |
| **Testing** | Write test cases, mock data | `capibara run "generate tests"` |
| **Automation** | Write scripts, handle edge cases | `capibara run "automate this task"` |

**Time saved**: Hours → Minutes ⚡

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

# Analyze your data
capibara run "Analyze this CSV file and find the top 10 customers by revenue" --execute

# Automate file processing
capibara run "Resize all images in this folder to 800x600 and save as WebP" --execute

# Create development tools
capibara run "Generate unit tests for this Python class with 90% coverage" --execute

# Process APIs
capibara run "Fetch data from this REST API and create a summary report" --execute

# List cached scripts
capibara list

# Show script details
capibara show <script_id>
```

## 🐍 Python SDK

```python
from capibara import CapibaraClient

# Initialize client
client = CapibaraClient(
    groq_api_key="your_groq_key",
    openai_api_key="your_openai_key"
)

# Analyze sales data
response = await client.run(
    prompt="Analyze this sales CSV and create a report with top products, revenue trends, and customer insights",
    language="python",
    execute=True
)

print(f"Script ID: {response.script_id}")
print(f"Generated Code: {response.code}")
print(f"Execution Result: {response.execution_result}")

# Process files
response = await client.run(
    prompt="Convert all PDF files in this directory to text and extract key information",
    language="python",
    execute=True
)
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

## 📊 Observability

Capibara Core provides comprehensive logging, metrics, and monitoring capabilities for production environments.

### 📝 Logging

**Structured JSON logs** with correlation IDs for easy analysis:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "capibara.core.engine",
  "event": "script_generated",
  "script_id": "sha256:abc123...",
  "language": "python",
  "provider": "openai",
  "duration_ms": 1250,
  "user_id": "user_123"
}
```

**Features:**
- **Structured logging** with `structlog`
- **Audit trail** for all security events
- **Configurable levels** (DEBUG, INFO, WARNING, ERROR)
- **File rotation** and retention policies
- **Multiple formats** (JSON, console)

**Configuration:**
```bash
# Set log level and format
export CAPIBARA_LOG_LEVEL=INFO
export CAPIBARA_LOG_FORMAT=json
export CAPIBARA_LOG_FILE=~/.capibara/logs/app.log
```

### 📈 Metrics

**Prometheus metrics** exposed at `/metrics` endpoint:

```bash
# Key metrics available:
capibara_script_generations_total{language="python", provider="openai", status="success"}
capibara_script_execution_duration_seconds{language="python"}
capibara_security_violations_total{rule_name="dangerous_import", severity="high"}
capibara_cache_operations_total{operation="get", result="hit"}
capibara_llm_requests_total{provider="openai", model="gpt-4", status="success"}
```

**Features:**
- **Comprehensive coverage**: Script generation, execution, cache, security, LLM usage
- **Real-time metrics** with configurable scrape intervals
- **Resource monitoring**: CPU, memory, disk usage
- **Business metrics**: Success rates, performance trends

### 🏥 Health Checks

**Multi-component health monitoring** at `/health` endpoint:

```bash
# Quick health check
curl http://localhost:8080/health

# Comprehensive health check
curl http://localhost:8080/health?full=true
```

**Monitored components:**
- ✅ **LLM Providers**: OpenAI, Groq connectivity and response times
- ✅ **Container Runtime**: Docker daemon status and resource availability
- ✅ **Cache System**: Cache directory and hit rates
- ✅ **Security Policies**: Policy files and rule availability
- ✅ **System Resources**: Memory, disk space, CPU usage

### 📊 Monitoring Stack

**Pre-configured monitoring** with Grafana dashboards:

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
```

**Included dashboards:**
- 📊 **System Overview**: Script generations, executions, cache performance
- 🔒 **Security Monitoring**: Violations, scan results, policy compliance
- ⚡ **Performance**: Response times, resource usage, bottlenecks
- 🏥 **Health Status**: Component status, dependencies, alerts

### 🔍 Troubleshooting

**Common monitoring commands:**

```bash
# Check system health
capibara doctor

# View recent logs
tail -f ~/.capibara/logs/app.log | jq '.'

# Check metrics
curl http://localhost:8080/metrics | grep capibara_script_generations_total

# Monitor health status
watch -n 5 'curl -s http://localhost:8080/health | jq .'
```

**Log locations:**
- Application logs: `~/.capibara/logs/app.log`
- Audit logs: `~/.capibara/logs/audit/audit.jsonl`
- Security violations: `~/.capibara/logs/audit/violations.jsonl`

## 📚 Real-World Examples

### 📊 Data Analysis
```bash
# Analyze sales performance
capibara run "Process this sales CSV, calculate monthly growth rates, identify seasonal patterns, and generate insights for the marketing team" --execute

# Customer segmentation
capibara run "Analyze customer data and segment users by behavior, value, and engagement level" --execute
```

### 🔧 Development Tools
```bash
# Code quality check
capibara run "Scan this Python project for code smells, security issues, and performance bottlenecks" --execute

# API testing
capibara run "Create comprehensive tests for this REST API endpoint with edge cases and error handling" --execute
```

### 📁 File Processing
```bash
# Image optimization
capibara run "Optimize all images in this folder: resize to max 1920px, compress to 80% quality, convert to WebP" --execute

# Document processing
capibara run "Extract text from all PDFs in this directory and create a searchable index" --execute
```

### 🌐 Web & APIs
```bash
# Price monitoring
capibara run "Scrape product prices from this e-commerce site and track changes over time" --execute

# Data pipeline
capibara run "Create a script to fetch data from multiple APIs, clean and merge the data, then store in a database" --execute
```

See the `examples/` directory for complete code examples.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.