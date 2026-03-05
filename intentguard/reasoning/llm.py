import json
import os
from litellm import completion
from typing import Dict, Any

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

    # Model fallbacks via litellm can be parameterized, but we'll use a local fallback or OpenAI default.
    model = os.environ.get("INTENTGUARD_MODEL", "gpt-3.5-turbo")

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} if "gpt" in model else None
        )
        content = response.choices[0].message.content
        data = json.loads(content)
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
