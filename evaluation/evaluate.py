from __future__ import annotations
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.services.engine import ClaimDecisionEngine

def run(cases,expected):
    engine=ClaimDecisionEngine(); rows=[]
    for case in cases:
        t=time.perf_counter(); out=engine.analyze(__import__('backend.models.schemas',fromlist=['ClaimCase']).ClaimCase.model_validate(case)); ms=(time.perf_counter()-t)*1000
        exp=expected.get(case['case_id'],{}).get('expected'); rows.append({'case_id':case['case_id'],'expected':exp,'actual':out.decision,'correct':out.decision==exp,'validation':out.validation.status,'retrieval':len(out.citations),'citation_pages':sorted({c.page for c in out.citations}),'ms':round(ms,1)})
    acc=sum(r['correct'] for r in rows)/len(rows) if rows else 0
    abst=[r for r in rows if r['actual']=='NEEDS_REVIEW']; return rows,acc,abst

if __name__=='__main__':
    pub=json.loads(Path('data/public_cases/public_test_cases.json').read_text()); custom=json.loads(Path('evaluation/custom_cases.json').read_text()); exp=json.loads(Path('evaluation/expected_public.json').read_text())
    rows,acc,abst=run(pub+custom,{**exp,**{c['case_id']: {'expected': ('NEEDS_REVIEW' if c['case_id']=='CUSTOM-004' else ('NOT_ADMISSIBLE' if c['case_id']=='CUSTOM-002' else ('ADMISSIBLE_WITH_LIMITS' if c['case_id'] in ('CUSTOM-003','CUSTOM-005') else 'ADMISSIBLE')))} for c in custom}})
    from evaluation.metrics import retrieval_metrics
    rm=retrieval_metrics(rows,json.loads(Path('evaluation/expected_sections.json').read_text()))
    print(json.dumps({'case_results':rows,'overall_accuracy':acc,'abstentions':[x['case_id'] for x in abst],'retrieval_metrics':rm},indent=2))
    Path('evaluation/results/latest.json').write_text(json.dumps({'case_results':rows,'overall_accuracy':acc,'abstentions':[x['case_id'] for x in abst],'retrieval_metrics':rm},indent=2))
