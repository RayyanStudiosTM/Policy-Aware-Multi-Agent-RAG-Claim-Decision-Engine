from __future__ import annotations
from dataclasses import dataclass
from ..models.schemas import ClaimCase
from ..retrieval.hybrid import HybridRetriever

@dataclass
class EvidenceResult:
    results:list[dict]

class PolicyEvidenceAgent:
    name='PolicyEvidenceAgent'
    def __init__(self,retriever:HybridRetriever): self.retriever=retriever
    def run(self,case:ClaimCase,plan):
        queries=[case.task, 'hospitalization coverage limits room doctor fees medicines ambulance', 'pre-existing disease waiting period 48 months portability', '30 days waiting period cataract day care eye surgery', 'domiciliary hospitalization 20% basic sum insured', 'pre-hospitalisation 30 days post hospitalisation 60 days', 'cosmetic aesthetic treatment exclusion experimental unproven treatment']
        seen={};
        for q in queries:
            for r in self.retriever.search(q,k=5,rerank_k=10): seen[r['chunk_id']]=r
        results=sorted(seen.values(),key=lambda x:x['rerank_score'],reverse=True)[:18]
        return EvidenceResult(results)
