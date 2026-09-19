from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from datetime import date
from ..models.schemas import ClaimCase

@dataclass
class CasePlan:
    dimensions:list[str]
    missing:list[str]
    facts:dict[str,Any]

class CaseAnalysisAgent:
    name='CaseAnalysisAgent'
    def run(self,case:ClaimCase)->CasePlan:
        missing=[]
        if not case.documents: missing.append('No claim documents were supplied.')
        if case.hospital.get('network_provider') is None: missing.append('Network-provider status is missing.')
        if case.evidence_context and case.evidence_context.get('hospital_registered') is None and not case.hospital.get('registered'):
            missing.append('Hospital registration/definition evidence is unresolved.')
        if case.evidence_context and case.evidence_context.get('medical_necessity_confirmed') is None:
            missing.append('Medical necessity is not confirmed.')
        dims=['eligibility/waiting periods','hospital or day-care definition','coverage/exclusions','category limits','pre/post-hospitalization windows']
        if case.treatment.get('pre_existing'): dims.insert(1,'pre-existing disease waiting period')
        if case.treatment.get('type')=='domiciliary': dims.insert(1,'domiciliary hospitalization conditions')
        if case.treatment.get('experimental'): dims.insert(1,'experimental/unproven treatment exclusion')
        return CasePlan(dims,missing,case.model_dump())
