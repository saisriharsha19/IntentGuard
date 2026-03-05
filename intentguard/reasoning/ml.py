import os
import pickle
import json
from pathlib import Path
from typing import Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
import numpy as np

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "cmd_classifier.pkl"

# Expanded training dataset for bootstrapping the model
BOOTSTRAP_DATA = [
    # ---- SAFE COMMANDS (Label 0) ----
    {"command": "cat file.txt", "context": "User is rendering a log file locally", "intent": "view file contents", "label": 0, "risk_level": 0.0},
    {"command": "cat /etc/os-release", "context": "Checking operating system version", "intent": "system info gathering", "label": 0, "risk_level": 0.0},
    {"command": "less /var/log/syslog", "context": "Paging through system logs", "intent": "log analysis", "label": 0, "risk_level": 0.0},
    {"command": "tail -n 100 server.log", "context": "Monitoring live log outputs", "intent": "monitor logs", "label": 0, "risk_level": 0.0},
    {"command": "head -n 20 data.csv", "context": "Previewing CSV data structure", "intent": "data inspection", "label": 0, "risk_level": 0.0},
    {"command": "grep 'error' log.txt", "context": "Searching for errors in application logs", "intent": "error debugging", "label": 0, "risk_level": 0.0},
    {"command": "sed 's/foo/bar/g' test.txt", "context": "Replacing text in a temporary file", "intent": "text manipulation", "label": 0, "risk_level": 0.1},
    {"command": "ls", "context": "Listing current directory contents", "intent": "directory traversal", "label": 0, "risk_level": 0.0},
    {"command": "cd /tmp", "context": "Changing directory to temporary storage", "intent": "navigation", "label": 0, "risk_level": 0.0},
    {"command": "pwd", "context": "Getting current working directory", "intent": "navigation", "label": 0, "risk_level": 0.0},
    {"command": "python main.py", "context": "Running application entrypoint", "intent": "execute code", "label": 0, "risk_level": 0.0},
    
    # ---- DESTRUCTIVE / RISKY COMMANDS (Label 1) ----
    {"command": "rm -rf /", "context": "Attempting to delete root filesystem", "intent": "critical system destruction", "label": 1, "risk_level": 1.0},
    {"command": "rm -rf /*", "context": "Attempting to delete all files in root", "intent": "critical system destruction", "label": 1, "risk_level": 1.0},
    {"command": "rm -rf ~", "context": "Attempting to delete user home directory", "intent": "critical data deletion", "label": 1, "risk_level": 0.95},
    {"command": "rm -rf ~/.ssh", "context": "Attempting to delete SSH keystore", "intent": "credential destruction", "label": 1, "risk_level": 0.9},
    {"command": "rm -rf node_modules", "context": "Wiping out entirely local dependency store", "intent": "mass folder deletion", "label": 1, "risk_level": 0.5},
    {"command": "chmod -R 777 /", "context": "Granting global access to root filesystem", "intent": "security compromise", "label": 1, "risk_level": 0.95},
    {"command": "kubectl delete namespace prod", "context": "Deleting production k8s namespace", "intent": "production teardown", "label": 1, "risk_level": 0.95},
    {"command": "terraform destroy", "context": "Destroying all provisioned infrastructure", "intent": "total infrastructure teardown", "label": 1, "risk_level": 0.95},
    {"command": ":(){ :|:& };:", "context": "Executing a shell fork bomb", "intent": "resource exhaustion attack", "label": 1, "risk_level": 1.0}
]

def train_bootstrap_model():
    """Trains a simple, lightweight model using hardcoded instances + rich metadata from JSON."""
    print("Training bootstrap ML model...")
    
    texts = [item["command"] for item in BOOTSTRAP_DATA]
    labels = [item["label"] for item in BOOTSTRAP_DATA]
    
    dataset_path = Path(__file__).parent / "generated_training_data.json"
    if dataset_path.exists():
        with open(dataset_path, "r") as f:
            generated_data = json.load(f)
            texts.extend([item["command"] for item in generated_data])
            labels.extend([item["label"] for item in generated_data])
    else:
        print(f"Warning: {dataset_path} not found. Training on core data only.")
        
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 6), max_features=1500)),
        ('clf', SGDClassifier(loss='log_loss', max_iter=1000, random_state=42)) 
    ])
    
    pipeline.fit(texts, labels)
    
    MODEL_DIR.mkdir(exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    print(f"Model saved to {MODEL_PATH}")

def predict_ml(command: str) -> Dict[str, Any]:
    """
    Predicts risk score of a command using the lightweight scikit-learn model.
    Latency is typically <10ms.
    """
    if not MODEL_PATH.exists():
        train_bootstrap_model()
        
    try:
        with open(MODEL_PATH, "rb") as f:
            pipeline = pickle.load(f)
            
        # Get probability of class 1 (risky)
        # Using [[]] to pass a single sample
        proba = pipeline.predict_proba([command])[0]
        risk_score = float(proba[1])  # probability of being destructive
        
        return {
            "ml_risk_score": round(risk_score, 2),
            "ml_confidence": float(np.max(proba))  # model's confidence in its own prediction
        }
    except Exception as e:
        # Fallback if model fails to load or execute
        return {
            "ml_risk_score": 0.0,
            "ml_confidence": 0.0,
            "error": str(e)
        }
