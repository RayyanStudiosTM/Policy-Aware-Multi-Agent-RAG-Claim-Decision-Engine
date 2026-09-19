from fastapi import FastAPI, HTTPException
from ..models.schemas import AnalyzeRequest, AnalysisResponse, ClaimCase
from ..services.engine import ClaimDecisionEngine
app=FastAPI(title='Aptino Policy-Aware Claim Decision Engine',version='1.0.0')
engine=None
@app.on_event('startup')
def startup():
    global engine; engine=ClaimDecisionEngine()
@app.get('/health')
def health(): return {'status':'ok','service':'aptino-claim-engine'}
@app.post('/analyze',response_model=AnalysisResponse)
def analyze(req:AnalyzeRequest):
    try: return engine.analyze(req.case)
    except Exception as e: raise HTTPException(status_code=400,detail=f'Analysis failed: {type(e).__name__}: {e}')
