import shlex
from typing import Dict, Any

def evaluate_rules(command: str) -> Dict[str, Any]:
    """
    Evaluates a command against static rules using shell semantics (shlex) for safer extraction.
    Returns a dict with matched, risk_score, intent, decision, confidence, and reason.
    """
    try:
        # Split but preserve quoting semantics to avoid naive regex evasion
        tokens = shlex.split(command)
    except Exception:
        # If shlex fails (unclosed quotes etc.), treat as potentially dangerous ambiguous syntax
        return {"matched": False}

    if not tokens:
        return {"matched": False}
        
    base_cmd = tokens[0]
    
    # 1. rm -rf detection
    if base_cmd == "rm":
        has_recursive = any(flag in ["-r", "-R", "-rf", "-fr", "--recursive"] for flag in tokens)
        has_force = any(flag in ["-f", "-rf", "-fr", "--force"] for flag in tokens)
        
        # Check targets
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        critical_targets = {"/", "/*", "~", "~/*", ".", "..", ".git"}
        
        if has_recursive and any(t in critical_targets for t in targets):
            return {
                "matched": True,
                "risk_score": 0.98,
                "intent": "critical destructive file deletion",
                "decision": "block",
                "confidence": 1.0,
                "reason": f"Matched recursive delete on critical system target: {command}"
            }
            
        elif has_recursive and has_force:
            return {
                "matched": True,
                "risk_score": 0.65,
                "intent": "forced recursive deletion",
                "decision": "warn",
                "confidence": 0.9,
                "reason": f"Matched recursive force delete context: {command}"
            }

    # 2. Terraform Destructive
    if base_cmd == "terraform" and len(tokens) > 1 and tokens[1] == "destroy":
        return {
            "matched": True,
            "risk_score": 0.95,
            "intent": "infrastructure destruction",
            "decision": "block",
            "confidence": 1.0,
            "reason": "Terraform destroy operation detected."
        }

    # 3. SQL Destructive (Drop database/table usually passed to psql/mysql)
    sql_tokens = [t.lower() for t in tokens]
    if "drop" in sql_tokens and ("database" in sql_tokens or "table" in sql_tokens):
         return {
            "matched": True,
            "risk_score": 0.95,
            "intent": "database destruction",
            "decision": "block",
            "confidence": 0.95,
            "reason": "DROP statement detected in command invocation."
        }
         
    # 4. Kubernetes Destructive
    if base_cmd == "kubectl" and len(tokens) > 2 and tokens[1] == "delete":
        if tokens[2] in ["namespace", "ns", "cluster"]:
            return {
                "matched": True,
                "risk_score": 0.90,
                "intent": "kubernetes infrastructure deletion",
                "decision": "block",
                "confidence": 0.95,
                "reason": f"Kubernetes destructive delete on {tokens[2]}."
            }
        else:
            return {
                "matched": True,
                "risk_score": 0.60,
                "intent": "kubernetes resource deletion",
                "decision": "warn",
                "confidence": 0.8,
                "reason": "Kubernetes standard resource deletion."
            }
            
    return {"matched": False}
