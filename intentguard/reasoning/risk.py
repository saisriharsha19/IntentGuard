def compute_final_risk(
    base_command_risk: float = 0.0,
    ml_model_risk: float = 0.0,
    llm_model_risk: float = 0.0,
    context_anomaly_score: float = 0.0,
    llm_confidence: float = 0.5
) -> float:
    """
    Computes final risk score using dynamically weighted factors.
    The rules provide the base_command_risk.
    The ML model provides the fast prediction.
    The BM25 engine provides context anomaly.
    The LLM provides nuanced risk.
    """
    # Base command rule evaluation is heavily trusted if it triggers at all.
    cmd_weight = 0.35
    
    # ML model weight
    ml_weight = 0.25
    
    # Context anomaly weight
    ctx_weight = 0.15
    
    # LLM weight scales with LLM confidence. 
    # If the LLM is unsure, we fall back heavily to the rules and ML.
    llm_weight = 0.25 * llm_confidence
    
    final_risk = (
        (base_command_risk * cmd_weight) +
        (ml_model_risk * ml_weight) +
        (context_anomaly_score * ctx_weight) +
        (llm_model_risk * llm_weight)
    )
    
    # Normalize heavily towards the highest single risk indicator.
    # If ANY system flags critical risk (>0.8), we want the final score to reflect that closely 
    # rather than being averaged out completely.
    max_individual_risk = max([base_command_risk, ml_model_risk, llm_model_risk])
    if max_individual_risk > 0.8:
        final_risk = max(final_risk, max_individual_risk)
    
    return max(0.0, min(final_risk, 1.0))

def determine_decision(risk_score: float) -> str:
    """
    Determine decision based on thresholds:
    0-0.4 allow
    0.4-0.7 warn
    >0.7 block
    """
    if risk_score > 0.7:
        return "block"
    elif risk_score > 0.4:
        return "warn"
    return "allow"
