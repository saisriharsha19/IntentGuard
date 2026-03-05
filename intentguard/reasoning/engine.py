import json
from typing import Dict, Any, Optional

from .rules import evaluate_rules
from .ml import predict_ml
from .context import get_pruned_context
from .llm import analyze_intent
from .risk import compute_final_risk, determine_decision

def analyze_action(command: str, user: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Advanced main reasoning pipeline:
    1. Advanced Rules Engine (shlex parsing)
    2. Lightweight ML Model Classification
    3. SOTA Context Pruning (BM25)
    4. LLM Analysis with pruned context
    5. Final Risk Scoring combination
    """
    
    # 1. Stage 1: Fast Rules
    rule_result = evaluate_rules(command)
    
    # If rules definitively catch an absolute blocker, we fast-path return.
    if rule_result.get("matched") and rule_result.get("risk_score", 0) > 0.9:
        return {
            "risk_score": rule_result["risk_score"],
            "intent": rule_result["intent"],
            "decision": rule_result["decision"],
            "reason": rule_result["reason"],
            "confidence": rule_result["confidence"]
        }
        
    base_command_risk = rule_result.get("risk_score", 0.1) if rule_result.get("matched") else 0.1
    
    # 2. Stage 2: Fast ML Classification
    ml_result = predict_ml(command)
    ml_model_risk = ml_result.get("ml_risk_score", 0.1)
    
    # 3. Stage 3: Context Pruning and Anomaly Detection
    context_data = get_pruned_context(current_command=command, user=user)
    context_anomaly_score = context_data.get("anomaly_score", 0.0)
    
    # Prepare pruned history text for LLM
    pruned_history_text = "\n".join([f"- Command: {h['command']} (Decision: {h['decision']}, Intent: {h['intent']})" for h in context_data.get("pruned_history", [])])
    
    # If there's external context passed in via HTTP, append it
    if context:
        pruned_history_text += f"\nExternal Context: {json.dumps(context)}"
        
    if not pruned_history_text.strip():
        pruned_history_text = "No relevant context found."
        
    # 4. Stage 4: LLM Analysis
    llm_result = analyze_intent(command, user, context=pruned_history_text)
    
    # Handle LLM failure gracefully without corrupting the average
    if llm_result.get("risk_score") is None:
        llm_model_risk = 0.0
        llm_confidence = 0.0
    else:
        llm_model_risk = llm_result.get("risk_score", 0.1)
        llm_confidence = llm_result.get("confidence", 0.5)
    
    # 5. Final Risk Calculation
    final_risk = compute_final_risk(
        base_command_risk=base_command_risk,
        ml_model_risk=ml_model_risk,
        llm_model_risk=llm_model_risk,
        context_anomaly_score=context_anomaly_score,
        llm_confidence=llm_confidence
    )
    
    decision = determine_decision(final_risk)
    
    # Combine reasons
    reasons = [rule_result.get("reason", "No rules triggered.")]
    reasons.append(f"ML Risk: {ml_model_risk}. Context Anomaly: {context_anomaly_score}.")
    reasons.append(llm_result.get("reason", "No LLM reason."))
    
    return {
        "risk_score": round(final_risk, 2),
        "intent": llm_result.get("intent", "Unknown (Advanced Engine)"),
        "decision": decision,
        "reason": " | ".join(reasons),
        "confidence": round(max([llm_confidence, rule_result.get("confidence", 0.0), ml_result.get("ml_confidence", 0.0)]), 2)
    }
