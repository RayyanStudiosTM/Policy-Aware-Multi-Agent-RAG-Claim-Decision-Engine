from __future__ import annotations
from ..models.schemas import Validation
class ValidationAgent:
    name='ValidationAgent'
    def run(self,case,decision,findings,limits,citations):
        supported={c.chunk_id for c in citations}; unsupported=[]
        for f in findings:
            if f.material and not set(f.citation_ids).intersection(supported): unsupported.append(f.conclusion)
        for l in limits:
            if not set(l.citation_ids).intersection(supported): unsupported.append(l.basis)
        if unsupported:
            return Validation(status='REVIEW',unsupported_claims=unsupported,revision_signal='Material statement lacks a traceable policy citation.')
        return Validation(status='PASS',unsupported_claims=[])
