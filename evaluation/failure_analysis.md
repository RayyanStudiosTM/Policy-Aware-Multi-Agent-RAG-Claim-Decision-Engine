# Failure Analysis

## Failure 1 — Hospital-definition evidence gap
**Scenario:** PUB-011 provides a facility name but no evidence that it is registered or satisfies the policy's minimum hospital criteria.  
**Risk:** a model could infer that a named facility is a Hospital.  
**Fix:** Case Analysis flags the missing evidence; Coverage marks the case `NEEDS_REVIEW`; Validation prevents a final supported decision when material evidence is absent.

## Failure 2 — Waiting-period precedence
**Scenario:** PUB-002 is an ordinary inpatient claim, but the claim date is inside the initial 30-day period.  
**Risk:** a generic coverage prompt could focus on hospitalization and miss the temporal exclusion.  
**Fix:** waiting-period checks run before ordinary limit calculations and can override an otherwise covered treatment.

## Failure 3 — Category caps hidden by a large Sum Insured
**Scenario:** PUB-007 has a ₹10 lakh Sum Insured, but professional fees, medicines/diagnostics, room and ambulance remain subject to separate policy caps.  
**Risk:** treating the Sum Insured as the only limit produces an overstated payable amount.  
**Fix:** Coverage & Exclusion calculates each documented category cap independently and exposes the deduction with policy citations.
