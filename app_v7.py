"""
THRONE Backend API v7
Flask server with all endpoints for hackathon demo
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import warnings
import os
import sys

warnings.filterwarnings('ignore')

# Import engine classes (needed for pickle deserialization)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from throne_engine_v7 import THRONEMasterEngine, RuleBasedEngine

app = Flask(__name__)
CORS(app)

# Load master engine
engine = pickle.load(open("throne_master_engine_v7.pkl", "rb"))
print(f"THRONE API v7 Online — {engine.name}")

# ── ENDPOINTS ──

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "THRONE AI v7 — Har Flush Ek Free Health Test", "status": "online"})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "THRONE AI Online",
        "version": "7.0",
        "models": f"{len(engine.models)} ML + Rule Engine",
        "diseases": "127+",
        "engine": engine.name
    })

@app.route("/scan", methods=["POST"])
def scan():
    data = request.json or {}
    strip = {
        "glucose":          data.get("glucose", 0),
        "protein":          data.get("protein", 0),
        "nitrites":         data.get("nitrites", 0),
        "leukocytes":       data.get("leukocytes", 0),
        "bilirubin":        data.get("bilirubin", 0),
        "urobilinogen":     data.get("urobilinogen", 0.2),
        "ph":               data.get("ph", 6.0),
        "specific_gravity": data.get("specific_gravity", 1.015),
        "ketones":          data.get("ketones", 0),
        "blood":            data.get("blood", 0),
        "temperature":      data.get("temperature", 36.5),
    }
    result = engine.analyze(strip)
    result['user'] = data.get('user', 'Unknown')
    return jsonify(result)

@app.route("/demo", methods=["GET"])
def demo():
    """Return all 6 preset demo scenarios with results"""
    scenarios = {
        'normal': {'glucose':0, 'protein':0, 'ph':6, 'specific_gravity':1.020, 'ketones':0, 'blood':0, 'bilirubin':0, 'urobilinogen':0.2, 'nitrites':0, 'leukocytes':0, 'temperature':36.5},
        'diabetes': {'glucose':4, 'protein':0, 'ph':5, 'specific_gravity':1.030, 'ketones':3, 'blood':0, 'bilirubin':0, 'urobilinogen':0.2, 'nitrites':0, 'leukocytes':0, 'temperature':36.5},
        'uti': {'glucose':0, 'protein':1, 'ph':8, 'specific_gravity':1.015, 'ketones':0, 'blood':1, 'bilirubin':0, 'urobilinogen':0.2, 'nitrites':2, 'leukocytes':3, 'temperature':37.8},
        'kidney': {'glucose':0, 'protein':3, 'ph':5, 'specific_gravity':1.035, 'ketones':0, 'blood':3, 'bilirubin':0, 'urobilinogen':0.2, 'nitrites':0, 'leukocytes':1, 'temperature':36.5},
        'liver': {'glucose':0, 'protein':0, 'ph':7, 'specific_gravity':1.020, 'ketones':0, 'blood':0, 'bilirubin':3, 'urobilinogen':3, 'nitrites':0, 'leukocytes':0, 'temperature':36.5},
        'dka': {'glucose':4, 'protein':1, 'ph':5, 'specific_gravity':1.035, 'ketones':4, 'blood':0, 'bilirubin':0, 'urobilinogen':0.2, 'nitrites':0, 'leukocytes':0, 'temperature':36.5},
    }
    results = {}
    for name, strip in scenarios.items():
        results[name] = engine.analyze(strip)
    return jsonify(results)

@app.route("/trend", methods=["POST"])
def trend():
    """7-day trend analysis with prediction"""
    data = request.json or {}
    current_score = data.get('score', 80)
    
    # Generate mock 7-day history with slight trend
    import random
    history = []
    base = current_score + 15
    for i in range(7):
        day_score = max(0, min(100, base - i * ((100 - current_score) / 14) + random.uniform(-3, 3)))
        history.append(round(day_score, 1))
    
    # Predict next 7 days
    slope = (history[-1] - history[0]) / 7
    predicted = []
    for i in range(7):
        pred = max(0, min(100, history[-1] + slope * (i + 1)))
        predicted.append(round(pred, 1))
    
    threshold_days = None
    if slope < -1:
        for i, p in enumerate(predicted):
            if p < 70:
                threshold_days = i + 1
                break
    
    return jsonify({
        'history': history,
        'predicted': predicted,
        'slope': round(slope, 2),
        'trend': 'DECLINING' if slope < -1 else 'STABLE' if abs(slope) <= 1 else 'IMPROVING',
        'threshold_days': threshold_days,
        'warning': f'Risk threshold may be reached in {threshold_days} days' if threshold_days else None
    })

@app.route("/sos", methods=["POST"])
def sos():
    """Emergency SOS alert chain"""
    data = request.json or {}
    return jsonify({
        'sos_triggered': True,
        'level': 1,
        'message': 'CRITICAL health risk detected',
        'chain': [
            {'level': 1, 'target': 'User', 'method': 'Push + Voice', 'time': '0 min'},
            {'level': 2, 'target': 'Family', 'method': 'SMS + WhatsApp', 'time': '5 min'},
            {'level': 3, 'target': 'ASHA Worker', 'method': 'Dashboard Alert', 'time': '10 min'},
            {'level': 4, 'target': 'PHC', 'method': 'Emergency Call', 'time': '15 min'},
        ],
        'patient': data.get('user', 'Unknown'),
        'diseases': data.get('diseases', []),
        'score': data.get('score', 0),
    })

@app.route("/chat", methods=["POST"])
def chat():
    """AI Doctor chat endpoint — uses Anthropic API"""
    try:
        import anthropic
        data = request.json or {}
        message = data.get("message", "")
        health = data.get("health_data", {})
        api_key = data.get("api_key", "")
        
        if not api_key:
            return jsonify({"reply": "API key required. Please enter your Anthropic/OpenAI API key."})
        
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system="Tu THRONE ka personal health assistant hai. Hindi mein baat karo. Simple language use karo. Medical diagnose mat karo — sirf guide karo. Patient ko daraa mat — calm rakho.",
            messages=[{"role": "user", "content": f"Health data: {health}\nUser question: {message}"}]
        )
        return jsonify({"reply": response.content[0].text})
    except ImportError:
        return jsonify({"reply": "Anthropic library not installed. Chat feature requires API key and anthropic package."})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

# ── RUN ──
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
