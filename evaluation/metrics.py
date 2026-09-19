from __future__ import annotations
import json
from pathlib import Path

def retrieval_metrics(rows, expected_sections):
    # Citation hit rate: a case receives credit when at least one expected policy page is cited.
    hits=0; total=0
    for r in rows:
        cid=r['case_id']; pages=r.get('citation_pages',[]); expected=expected_sections.get(cid,[])
        if not expected:
            continue
        total += 1
        if set(pages)&set(expected): hits += 1
    return {'case_level_citation_hit_rate': hits/total if total else 0, 'cases_with_expected_page_citation': hits, 'cases_evaluated': total}
