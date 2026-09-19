from __future__ import annotations
from typing import TypedDict, Any
from .case_analysis import CaseAnalysisAgent
from .evidence import PolicyEvidenceAgent
from .coverage import CoverageExclusionAgent
from .decision import DecisionAgent
from .validation import ValidationAgent

class ClaimState(TypedDict, total=False):
    case: Any
    plan: Any
    evidence: Any
    coverage: Any
    decision: str
    validation: Any


def build_graph(agents):
    """Build an explicit LangGraph state machine when LangGraph is installed."""
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return None
    graph=StateGraph(ClaimState)
    graph.add_node('case_analysis', lambda s: {'plan':agents['case'].run(s['case'])})
    graph.add_node('policy_evidence', lambda s: {'evidence':agents['evidence'].run(s['case'],s['plan'])})
    graph.add_node('coverage_exclusion', lambda s: {'coverage':agents['coverage'].run(s['case'],s['evidence'])})
    graph.add_node('decision', lambda s: {'decision':agents['decision'].run(s['case'],s['coverage'],s['evidence'])})
    graph.add_node('validation', lambda s: {'validation':agents['validation'].run(s['case'],s['decision'],s['coverage'].findings,s['coverage'].limits,[])})
    graph.set_entry_point('case_analysis')
    graph.add_edge('case_analysis','policy_evidence'); graph.add_edge('policy_evidence','coverage_exclusion')
    graph.add_edge('coverage_exclusion','decision'); graph.add_edge('decision','validation'); graph.add_edge('validation',END)
    return graph.compile()
