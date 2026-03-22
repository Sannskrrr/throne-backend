from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import warnings
import os
import sys

warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from throne_engine_v7 import THRONEMasterEngine, RuleBasedEngine

app = Flask(__name__)
CORS(app)

# Build engine fresh instead of loading pickle (avoids 14MB file)
engine = THRONEMasterEngine(models_dir='.')
print("THRONE API v7 Online")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "THRONE AI v7", "status": "online"})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "THRONE AI Online", "version": "7.0", "models": f"{len(engine.models)} ML + Rule Engine", "diseases": "127+"})

@app.route("/scan", methods=["POST"])
def scan():
    data = request.json or {}
    strip = {k: data.get(k, d) for k, d in [("glucose",0),("protein",0),("nitrites",0),("leukocytes",0),("bilirubin",0),("urobilinogen",0.2),("ph",6.0),("specific_gravity",1.015),("ketones",0),("blood",0),("temperature",36.5)]}
    result = engine.analyze(strip)
    result['user'] = data.get('user', 'Unknown')
    return jsonify(result)

@app.route("/demo", methods=["GET"])
def demo():
    scenarios = {
        'normal': {'glucose':0,'protein':0,'ph':6,'specific_gravity':1.020,'ketones':0,'blood':0,'bilirubin':0,'urobilinogen':0.2,'nitrites':0,'leukocytes':0,'temperature':36.5},
        'diabetes': {'glucose':4,'protein':0,'ph':5,'specific_gravity':1.030,'ketones':3,'blood':0,'bilirubin':0,'urobilinogen':0.2,'nitrites':0,'leukocytes':0,'temperature':36.5},
        'uti': {'glucose':0,'protein':1,'ph':8,'specific_gravity':1.015,'ketones':0,'blood':1,'bilirubin':0,'urobilinogen':0.2,'nitrites':2,'leukocytes':3,'temperature':37.8},
        'kidney': {'glucose':0,'protein':3,'ph':5,'specific_gravity':1.035,'ketones':0,'blood':3,'bilirubin':0,'urobilinogen':0.2,'nitrites':0,'leukocytes':1,'temperature':36.5},
        'liver': {'glucose':0,'protein':0,'ph':7,'specific_gravity':1.020,'ketones':0,'blood':0,'bilirubin':3,'urobilinogen':3,'nitrites':0,'leukocytes':0,'temperature':36.5},
        'dka': {'glucose':4,'protein':1,'ph':5,'specific_gravity':1.035,'ketones':4,'blood':0,'bilirubin':0,'urobilinogen':0.2,'nitrites':0,'leukocytes':0,'temperature':36.5},
    }
    return jsonify({k: engine.analyze(v) for k, v in scenarios.items()})

@app.route("/trend", methods=["POST"])
def trend():
    data = request.json or {}
    score = data.get('score', 80)
    import random
    hist = [max(0,min(100, score+15-i*((100-score)/14)+random.uniform(-3,3))) for i in range(7)]
    slope = (hist[-1]-hist[0])/7
    pred = [max(0,min(100, hist[-1]+slope*(i+1))) for i in range(7)]
    td = None
    if slope < -1:
        for i,p in enumerate(pred):
            if p < 70: td = i+1; break
    return jsonify({'history':[round(h,1) for h in hist],'predicted':[round(p,1) for p in pred],'slope':round(slope,2),'trend':'DECLINING' if slope<-1 else 'STABLE' if abs(slope)<=1 else 'IMPROVING','threshold_days':td})

@app.route("/sos", methods=["POST"])
def sos():
    data = request.json or {}
    return jsonify({'sos_triggered':True,'chain':[{'level':1,'target':'User','method':'Push+Voice','time':'0 min'},{'level':2,'target':'Family','method':'SMS+WhatsApp','time':'5 min'},{'level':3,'target':'ASHA Worker','method':'Dashboard','time':'10 min'},{'level':4,'target':'PHC','method':'Emergency Call','time':'15 min'}],'patient':data.get('user','Unknown'),'score':data.get('score',0)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
