import json
from pathlib import Path
from backend.models.schemas import ClaimCase
from backend.services.engine import ClaimDecisionEngine

def test_public_key_cases():
    cases=json.loads(Path('data/public_cases/public_test_cases.json').read_text())
    eng=ClaimDecisionEngine()
    expected={'PUB-001':'ADMISSIBLE_WITH_LIMITS','PUB-002':'NOT_ADMISSIBLE','PUB-003':'NOT_ADMISSIBLE','PUB-004':'ADMISSIBLE_WITH_LIMITS','PUB-005':'ADMISSIBLE','PUB-006':'NEEDS_REVIEW','PUB-007':'ADMISSIBLE_WITH_LIMITS','PUB-008':'NOT_ADMISSIBLE','PUB-009':'ADMISSIBLE','PUB-010':'ADMISSIBLE','PUB-011':'NEEDS_REVIEW','PUB-012':'NOT_ADMISSIBLE'}
    for c in cases:
        assert eng.analyze(ClaimCase.model_validate(c)).decision==expected[c['case_id']]
