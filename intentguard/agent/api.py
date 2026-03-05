from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from intentguard.reasoning.engine import analyze_action
from intentguard.storage.db import log_action

app = FastAPI(title="IntentGuard Agent Core", version="0.1.0")

class AnalyzeRequest(BaseModel):
    action_type: str
    command: str
    user: str
    timestamp: float

class AnalyzeResponse(BaseModel):
    risk_score: float
    intent: str
    decision: str
    message: str

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    try:
        # Run core reasoning
        result = analyze_action(command=request.command, user=request.user)
        
        # Prepare response
        decision = result["decision"]
        risk_score = float(result["risk_score"])
        intent = result["intent"]
        reason = result.get("reason", "")
        
        # Craft user-friendly message based on decision
        if decision == "block":
            msg = f"IntentGuard blocked this action (Risk: {risk_score}): {intent}. {reason}"
        elif decision == "warn":
            msg = f"⚠ IntentGuard Warning (Risk: {risk_score}): {intent}. {reason}"
        else:
            msg = "Action allowed."
            
        # Log to local history db
        # Note: In a warn scenario, user_confirmed starts as False until the interceptor re-posts or updates it
        log_action(
            command=request.command,
            user=request.user,
            timestamp=request.timestamp,
            risk_score=risk_score,
            decision=decision,
            user_confirmed=True if decision == "allow" else False,
            intent=intent
        )
        
        return AnalyzeResponse(
            risk_score=risk_score,
            intent=intent,
            decision=decision,
            message=msg
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    # Placeholder for Prometheus metrics
    return {"status": "ok"}
