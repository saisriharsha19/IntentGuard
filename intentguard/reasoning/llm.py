import json
import os
import re
from litellm import completion
from typing import Dict, Any

def try_parse_json(text: str) -> Dict[str, Any]:
    """
    Attempts to parse JSON out of an LLM response robustly.
    Handles raw JSON, markdown-wrapped JSON, and plain text.
    """
    text = text.strip()
    # Try parsing the raw text directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    # Look for a json markdown block
    json_blocks = re.findall(r'```json\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
    if json_blocks:
        try:
            return json.loads(json_blocks[0].strip())
        except json.JSONDecodeError:
            pass
            
    # Look for any markdown block
    any_blocks = re.findall(r'```\n(.*?)\n```', text, re.DOTALL)
    if any_blocks:
        try:
            return json.loads(any_blocks[0].strip())
        except json.JSONDecodeError:
            pass
            
    # Attempt to find the first `{` and last `}`
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(text[start_idx:end_idx+1])
        except json.JSONDecodeError:
            pass

    return {}


def analyze_intent(command: str, user: str, context: str = "") -> Dict[str, Any]:
    """
    Analyzes intent using LiteLLM.
    Returns intent, risk_score, confidence, and recommended action.
    """
    prompt = f"""
You are a security reasoning system reviewing a CLI command.

Command details:
- Command: {command}
- User: {user}

Relevant Historical Context (Pruned via BM25):
{context}

Analyze the command and return a JSON object with the following fields:
- intent: (string) A short description of what the user is trying to do
- risk_score: (float) 0.0 to 1.0 (where >0.7 is block, >0.4 is warn)
- confidence: (float) 0.0 to 1.0 
- recommended_action: (string) allow, warn, or block
- reason: (string) Explanation of the decision

Only output valid JSON format.
"""

    model = os.environ.get("INTENTGUARD_MODEL", "gpt-3.5-turbo")
    api_base = os.environ.get("INTENTGUARD_API_BASE", None)
    api_key = os.environ.get("INTENTGUARD_API_KEY", None)

    # Prepare litellm args
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    
    if api_base:
        kwargs["api_base"] = api_base
        
    if api_key:
        kwargs["api_key"] = api_key
        
    # Use json mode if we strictly know it's a provider that supports it
    if "gpt" in model.lower() and not model.startswith("ollama/"):
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = completion(**kwargs)
        content = response.choices[0].message.content
        data = try_parse_json(content)
        
        # Ensure mapping of fields exists
        return {
            "intent": data.get("intent", "Unknown"),
            "risk_score": float(data.get("risk_score", 0.5)),
            "confidence": float(data.get("confidence", 0.5)),
            "decision": data.get("recommended_action", "warn"),
            "reason": data.get("reason", "No reason provided")
        }
    except Exception as e:
        # Fallback in case LLM fails or API key is missing
        # We shouldn't guess risk if the LLM crashes. Let the Rules + ML engines handle it.
        return {
            "intent": "unknown",
            "risk_score": None, # Signal that LLM analysis failed gracefully
            "confidence": 0.0,
            "decision": "unknown",
            "reason": f"LLM analysis skipped: {str(e)}"
        }
