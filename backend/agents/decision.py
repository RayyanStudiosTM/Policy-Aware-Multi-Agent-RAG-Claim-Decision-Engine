from __future__ import annotations
from ..models.schemas import Finding, Citation, Limit, Validation
class DecisionAgent:
    name='DecisionAgent'
    def run(self,case,coverage,evidence):
        # Hard safety policy: exclusions/waiting periods override ordinary limits; unresolved evidence abstains.
        decision=coverage.hard_decision or 'NEEDS_REVIEW'
        return decision
