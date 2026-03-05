from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import shlex

from intentguard.storage.db import get_recent_actions

def get_pruned_context(
    current_command: str,
    user: str,
    top_k: int = 5,
    max_history: int = 100
) -> Dict[str, Any]:
    """
    Implements SOTA Context Pruning using BM25.
    Retrieves only the most semantically relevant operations from the user's history
    to pass to the LLM, reducing context rot and token usage.
    """
    recent_actions = get_recent_actions(limit=max_history)
    
    if not recent_actions:
        return {
            "pruned_history": [],
            "anomaly_score": 0.0,
            "message": "No history found."
        }
        
    # Filter actions by the specific user
    user_actions = [a for a in recent_actions if a['user'] == user]
    
    if not user_actions:
        return {
            "pruned_history": [],
            "anomaly_score": 0.0,
            "message": "No history found for user."
        }
        
    # Tokenize history for BM25
    # BM25 works best on word/token boundaries
    tokenized_corpus = []
    for action in user_actions:
        try:
            tokens = shlex.split(action['command'])
        except:
            tokens = action['command'].split()
        tokenized_corpus.append(tokens)

    bm25 = BM25Okapi(tokenized_corpus)
    
    try:
        current_tokens = shlex.split(current_command)
    except:
        current_tokens = current_command.split()

    # Get scores for the current command against history corpus
    doc_scores = bm25.get_scores(current_tokens)
    
    # Calculate anomaly: If maximum score is very low, this command is anomalous
    # i.e., the user has rarely/never done something similar before
    max_score = float(max(doc_scores)) if len(doc_scores) > 0 else 0.0
    
    # Simple normalizer for BM25 anomaly (higher max_score = lower anomaly)
    # BM25 scores can be arbitrarily high, but we'll cap the inverse mapping.
    anomaly_score = 1.0 - min(max_score / 10.0, 1.0)
    
    # Retrieve top-k most relevant documents
    # rank-bm25 automatically sorts by score descending
    top_actions = bm25.get_top_n(current_tokens, user_actions, n=top_k)
    
    return {
        "pruned_history": top_actions,
        "bm25_max_score": max_score,
        "anomaly_score": round(anomaly_score, 2),
        "message": f"Retrieved top {len(top_actions)} relevant actions to augment LLM context."
    }
