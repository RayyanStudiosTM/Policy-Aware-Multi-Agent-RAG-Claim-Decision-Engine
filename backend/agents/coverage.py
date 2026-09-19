from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from ..models.schemas import ClaimCase, Finding, Limit

@dataclass
class CoverageResult:
    findings:list[Finding]
    limits:list[Limit]
    missing:list[str]
    hard_decision:str|None
    confidence:float

class CoverageExclusionAgent:
    name='CoverageExclusionAgent'
    def run(self,case:ClaimCase,evidence)->CoverageResult:
        findings=[]; limits=[]; missing=[]; hard=None; conf=0.9
        si=float(case.sum_insured_inr); t=case.treatment; ex=case.expenses_inr
        def cite(page,section,claim):
            matches=[r for r in evidence.results if r['page']==page]
            return [matches[0]['chunk_id']] if matches else []
        # Evidence gaps first: these require abstention rather than guessing.
        if case.evidence_context and case.evidence_context.get('hospital_registered') is None and not case.hospital.get('registered'):
            missing.append('Proof that the facility satisfies the policy definition of Hospital is required (registration/minimum criteria).')
            findings.append(Finding(dimension='hospital definition',conclusion='The supplied evidence does not establish that the facility satisfies the policy definition of Hospital.',citation_ids=cite(3,'Hospital','hospital definition')))
        if case.evidence_context and case.evidence_context.get('medical_necessity_confirmed') is None:
            missing.append('Medical necessity should be established from medical records/doctor evidence before final adjudication.')
            findings.append(Finding(dimension='medical necessity',conclusion='Medical necessity is not established by the supplied evidence.',citation_ids=cite(3,'Hospitalization','medical necessity')))
        if missing:
            hard='NEEDS_REVIEW'; conf=0.97
        # Waiting periods
        try:
            start=date.fromisoformat(case.policy_start_date); claim=date.fromisoformat(case.claim_date); days=(claim-start).days
        except Exception: days=99999
        if days<30 and case.continuous_coverage_months==0 and case.prior_insurer_continuous_years==0:
            findings.append(Finding(dimension='initial waiting period',conclusion='Claim occurs within the 30-day waiting period and no continuity exception is evidenced.',citation_ids=cite(9,'30 days Waiting Period','30-day waiting period')))
            hard='NOT_ADMISSIBLE'; conf=0.99
        # PED
        if t.get('pre_existing'):
            waiting_months=48-max(0,int(case.prior_insurer_continuous_years)*12)
            if case.prior_insurer_continuous_years>=4 or case.continuous_coverage_months>=48:
                findings.append(Finding(dimension='pre-existing disease',conclusion='48-month continuous-coverage waiting period has elapsed.',citation_ids=cite(8,'WHAT WE EXCLUDE','pre-existing diseases')))
            else:
                findings.append(Finding(dimension='pre-existing disease',conclusion=f'Pre-existing disease remains within the policy waiting period; {waiting_months} months remain after applicable prior-coverage reduction.',citation_ids=cite(8,'WHAT WE EXCLUDE','pre-existing diseases')))
                hard='NOT_ADMISSIBLE'; conf=0.99
        # Specific exclusion
        if t.get('experimental'):
            findings.append(Finding(dimension='exclusion',conclusion='The supplied facts classify the treatment as experimental; the policy excludes unproven/experimental treatment.',citation_ids=cite(9,'WHAT WE EXCLUDE','unproven experimental')))
            hard='NOT_ADMISSIBLE'; conf=0.99
        diag=str(t.get('diagnosis','')).lower(); proc=str(t.get('procedure','')).lower()
        if 'cosmetic' in diag or 'cosmetic' in proc:
            findings.append(Finding(dimension='exclusion',conclusion='Cosmetic/aesthetic treatment is listed in the policy exclusions.',citation_ids=cite(9,'WHAT WE EXCLUDE','cosmetic aesthetic')))
            hard='NOT_ADMISSIBLE'; conf=0.99
        # Domiciliary
        if t.get('type')=='domiciliary':
            qualifies=bool(t.get('patient_cannot_be_moved') or t.get('hospital_room_unavailable'))
            if not qualifies:
                findings.append(Finding(dimension='domiciliary definition',conclusion='The supplied facts do not establish either policy condition for domiciliary treatment.',citation_ids=cite(2,'Domiciliary Treatment','domiciliary conditions'))); hard='NOT_ADMISSIBLE'; conf=0.98
            else:
                allowed=.20*si; claimed=sum(float(v or 0) for v in ex.values()); ded=max(0,claimed-allowed)
                limits.append(Limit(name='Domiciliary hospitalization aggregate sub-limit',allowed_inr=allowed,claimed_inr=claimed,deduction_inr=ded,basis='20% of Basic Sum Insured',citation_ids=cite(7,'SCOPE OF COVER','domiciliary sub-limit')))
                findings.append(Finding(dimension='domiciliary definition',conclusion='The supplied facts establish a qualifying domiciliary circumstance.',citation_ids=cite(2,'Domiciliary Treatment','domiciliary conditions')))
        # Day care / hospital stay
        if t.get('type')=='day_care' or (t.get('type') not in ('domiciliary',) and float(t.get('admission_hours',0))<24):
            if 'cataract' in diag or 'eye surgery' in proc:
                findings.append(Finding(dimension='day-care treatment',conclusion='Eye surgery is expressly listed among treatments for which the 24-hour minimum can be waived.',citation_ids=cite(7,'SCOPE OF COVER','Eye Surgery')))
            elif float(t.get('admission_hours',0))<24:
                findings.append(Finding(dimension='day-care treatment',conclusion='Less-than-24-hour treatment requires the policy conditions for a waiver/day-care treatment to be established.',citation_ids=cite(7,'SCOPE OF COVER','less than 24 hours')))
                if not (t.get('specialised_infrastructure') or t.get('technological_advance')): missing.append('Evidence of the policy conditions permitting less-than-24-hour treatment is required.')
        # First-year disease waiting: cataract
        if 'cataract' in diag and (case.continuous_coverage_months>=12 or case.prior_insurer_continuous_years>=1):
            if case.prior_insurer_continuous_years>=1 and case.prior_policy and case.prior_policy.get('database_and_claim_history_received'):
                findings.append(Finding(dimension='first-year disease waiting period',conclusion='The one-year cataract waiting period is waived by at least one completed year of continuous prior Indian individual health coverage, with prior claim-history evidence supplied.',citation_ids=cite(9,'Hospitalization expense incurred in the first year','cataract waiting waiver')))
        if 'cataract' in diag and case.continuous_coverage_months<12 and case.prior_insurer_continuous_years<1:
            findings.append(Finding(dimension='first-year disease waiting period',conclusion='Cataract treatment is subject to the first-year waiting period absent the documented continuity exception.',citation_ids=cite(9,'Hospitalization expense incurred in the first year','cataract'))); hard='NOT_ADMISSIBLE'; conf=.99
        # Limits for normal hospitalization. Use admitted hours for day count only when >=24.
        if t.get('type') in ('inpatient','day_care') and hard!='NOT_ADMISSIBLE':
            days=max(1,round(float(t.get('admission_hours',0))/24)) if float(t.get('admission_hours',0))>=24 else 0
            room_claim=float(ex.get('room',0)); room_allowed=.01*si*days if days else 0
            if room_claim>room_allowed and room_allowed>0:
                limits.append(Limit(name='Normal room expense',allowed_inr=room_allowed,claimed_inr=room_claim,deduction_inr=room_claim-room_allowed,basis='1% of Basic Sum Insured per day',citation_ids=cite(7,'SCOPE OF COVER','normal room expenses')))
            doctor=float(ex.get('doctor_fees',0)); da=.25*si
            if doctor>da: limits.append(Limit(name='Medical practitioner/consultant fees',allowed_inr=da,claimed_inr=doctor,deduction_inr=doctor-da,basis='25% of Sum Insured',citation_ids=cite(7,'SCOPE OF COVER','25% fees')))
            meds=float(ex.get('medicines_diagnostics',0)); ma=.40*si
            if meds>ma: limits.append(Limit(name='Medicines/diagnostics and similar expenses',allowed_inr=ma,claimed_inr=meds,deduction_inr=meds-ma,basis='40% of Sum Insured',citation_ids=cite(7,'SCOPE OF COVER','40% medicines diagnostics')))
            amb=float(ex.get('ambulance',0)); aa=min(.01*si,1000)
            if amb>aa: limits.append(Limit(name='Ambulance charges',allowed_inr=aa,claimed_inr=amb,deduction_inr=amb-aa,basis='1% of Basic Sum Insured or Rs 1000, whichever is less',citation_ids=cite(8,'Additional Benefits','ambulance')))
            if case.expense_timing:
                pre=int(case.expense_timing.get('pre_hospitalization_days_before_admission',0)); post=int(case.expense_timing.get('post_hospitalization_days_after_discharge',0));
                if pre>30: missing.append('Pre-hospitalization expense timing exceeds the stated 30-day policy window.')
                if post>60: missing.append('Post-hospitalization expense timing exceeds the stated 60-day policy window.')
                findings.append(Finding(dimension='pre/post hospitalization',conclusion=f'Pre-hospitalization evidence is {pre} days before admission and post-hospitalization evidence is {post} days after discharge; policy windows are 30 and 60 days respectively.',citation_ids=cite(8,'Additional Benefits','pre post windows')))
        # If evidence gaps only, review; otherwise limits determine status.
        if missing and hard is None: hard='NEEDS_REVIEW'; conf=.96
        if hard is None: hard='ADMISSIBLE_WITH_LIMITS' if any(l.deduction_inr>0 for l in limits) else 'ADMISSIBLE'
        return CoverageResult(findings,limits,missing,hard,conf)
