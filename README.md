# IntentGuard

**Agentic AI System That Prevents Costly Digital Mistakes**

IntentGuard is a lightweight local agent that intercepts risky user actions, reasons about intent, and prevents destructive mistakes before execution.

## Installation

```bash
pip install intentguard
intentguard init
```

## Usage

```bash
# Start the background agent
intentguard start

# Execute a command through IntentGuard protection
intentguard exec rm -rf /data
```

## LLM Configuration

IntentGuard uses LiteLLM under the hood, allowing you to use almost any LLM provider (OpenAI, Anthropic, Groq, Ollama, etc.) just by setting a few environment variables.

### Environment Variable Syntax

- **Linux/macOS (Bash/Zsh)**: `export INTENTGUARD_MODEL="model_name"`
- **Windows (PowerShell)**: `$env:INTENTGUARD_MODEL="model_name"`

### OpenAI

```bash
# Linux/macOS
export INTENTGUARD_MODEL="gpt-4o"
export INTENTGUARD_API_KEY="sk-..."

# Windows PowerShell
$env:INTENTGUARD_MODEL="gpt-4o"
$env:INTENTGUARD_API_KEY="sk-..."
```

### Anthropic

```bash
# Linux/macOS
export INTENTGUARD_MODEL="claude-3-5-sonnet-20240620"
export INTENTGUARD_API_KEY="sk-ant-..."

# Windows PowerShell
$env:INTENTGUARD_MODEL="claude-3-5-sonnet-20240620"
$env:INTENTGUARD_API_KEY="sk-ant-..."
```

### Groq

```bash
# Linux/macOS
export INTENTGUARD_MODEL="groq/llama3-8b-8192"
export INTENTGUARD_API_KEY="gsk_..."

# Windows PowerShell
$env:INTENTGUARD_MODEL="groq/llama3-8b-8192"
$env:INTENTGUARD_API_KEY="gsk_..."
```

### Local (Ollama)

If you are running Ollama locally, you can specify the base URL and the model name:

```bash
# Linux/macOS
export INTENTGUARD_MODEL="ollama/llama3"
export INTENTGUARD_API_BASE="http://localhost:11434"

# Windows PowerShell
$env:INTENTGUARD_MODEL="ollama/llama3"
$env:INTENTGUARD_API_BASE="http://localhost:11434"
```
