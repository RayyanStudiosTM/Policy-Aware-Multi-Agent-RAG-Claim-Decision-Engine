from __future__ import annotations
import json,time
from pathlib import Path
from ..models.schemas import *
from ..rag.ingest import chunk_policy
from ..retrieval.hybrid import build_index
from ..agents.case_analysis import CaseAnalysisAgent
from ..agents.evidence import PolicyEvidenceAgent
from ..agents.coverage import CoverageExclusionAgent
from ..agents.decision import DecisionAgent
from ..agents.validation import ValidationAgent
from ..agents.graph import build_graph

class ClaimDecisionEngine:
    def __init__(self):
        chunks_path=Path('policy/processed/chunks.json')
        pdf=Path('policy/source/USGIC-CSCIndividualHealthInsurance_2017-2018.pdf')
        if not chunks_path.exists(): chunk_policy(str(pdf),str(chunks_path))
        chunks=json.loads(chunks_path.read_text(encoding='utf-8'))
        self.retriever=build_index(str(chunks_path))
        self.case_agent=CaseAnalysisAgent(); self.evidence_agent=PolicyEvidenceAgent(self.retriever)
        self.coverage_agent=CoverageExclusionAgent(); self.decision_agent=DecisionAgent(); self.validation_agent=ValidationAgent()
    def analyze(self,case:ClaimCase)->AnalysisResponse:
        trace=[]
        graph=build_graph({'case':self.case_agent,'evidence':self.evidence_agent,'coverage':self.coverage_agent,'decision':self.decision_agent,'validation':self.validation_agent})
        if graph is not None:
            t0=time.perf_counter(); state=graph.invoke({'case':case}); total=(time.perf_counter()-t0)*1000
            plan=state['plan']; ev=state['evidence']; cov=state['coverage']; decision=state['decision']
            # LangGraph owns orchestration; the trace records auditable node completion, not hidden reasoning.
            trace=[AgentTrace(agent=self.case_agent.name,action='LangGraph node: structured case analysis',duration_ms=total/5),
                   AgentTrace(agent=self.evidence_agent.name,action='LangGraph node: hybrid retrieval + fusion + reranking',duration_ms=total/5,retrieval_count=len(ev.results)),
                   AgentTrace(agent=self.coverage_agent.name,action='LangGraph node: policy coverage/exclusion analysis',duration_ms=total/5),
                   AgentTrace(agent=self.decision_agent.name,action='LangGraph node: structured decision',duration_ms=total/5)]
        else:
            t0=time.perf_counter(); plan=self.case_agent.run(case); trace.append(AgentTrace(agent=self.case_agent.name,action='Fallback state-machine node: extracted facts and investigation plan',duration_ms=(time.perf_counter()-t0)*1000))
            t=time.perf_counter(); ev=self.evidence_agent.run(case,plan); trace.append(AgentTrace(agent=self.evidence_agent.name,action='Fallback state-machine node: hybrid dense+BM25 retrieval, RRF fusion and reranking',duration_ms=(time.perf_counter()-t)*1000,retrieval_count=len(ev.results)))
            t=time.perf_counter(); cov=self.coverage_agent.run(case,ev); trace.append(AgentTrace(agent=self.coverage_agent.name,action='Fallback state-machine node: coverage, exclusions, waiting periods and limits',duration_ms=(time.perf_counter()-t)*1000))
            t=time.perf_counter(); decision=self.decision_agent.run(case,cov,ev); trace.append(AgentTrace(agent=self.decision_agent.name,action='Fallback state-machine node: structured decision',duration_ms=(time.perf_counter()-t)*1000))
        needed=set(x for f in cov.findings for x in f.citation_ids) | set(x for l in cov.limits for x in l.citation_ids)
        cmap={r['chunk_id']:r for r in ev.results}
        citations=[]
        for cid in needed:
            r=cmap.get(cid)
            if not r:
                allchunks={c['chunk_id']:c for c in self.retriever.chunks}; r=allchunks.get(cid)
            if r: citations.append(Citation(claim='Policy evidence used by decision',page=r['page'],section=r['section'],chunk_id=r['chunk_id'],excerpt=r['text'][:500]))
        t=time.perf_counter(); val=self.validation_agent.run(case,decision,cov.findings,cov.limits,citations); trace.append(AgentTrace(agent=self.validation_agent.name,action='Checked material findings and limits for policy citations',duration_ms=(time.perf_counter()-t)*1000,status=val.status))
        if val.status!='PASS': decision='NEEDS_REVIEW'
        claimed=sum(float(v or 0) for v in case.expenses_inr.values())
        deductions=sum(l.deduction_inr for l in cov.limits)
        payable=max(0,claimed-deductions) if decision not in ('NOT_ADMISSIBLE','NEEDS_REVIEW') else (0 if decision=='NOT_ADMISSIBLE' else None)
        return AnalysisResponse(case_id=case.case_id,decision=decision,confidence=cov.confidence,key_findings=cov.findings,applicable_limits=cov.limits,missing_evidence=cov.missing,citations=citations,validation=val,trace=trace,payable_estimate_inr=payable)

