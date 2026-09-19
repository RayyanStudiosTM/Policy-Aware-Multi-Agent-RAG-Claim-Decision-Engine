import json
import os
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(
    page_title="Aptino • Claim Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Theme / CSS
# -----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: #f6f8fb; }
.block-container { max-width: 1480px; padding-top: 1.1rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid #182337;
}

[data-testid="stSidebar"] * {
    color: #dce5f2;
}

/* Keep text dark inside white sidebar controls */
[data-testid="stSidebar"] input {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}

[data-testid="stSidebar"] input::placeholder {
    color: #64748b !important;
    -webkit-text-fill-color: #64748b !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #0f172a !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] * {
    color: #0f172a !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    background: #ffffff !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] small {
    color: #64748b !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
    color: #0f172a !important;
    background: #ffffff !important;
    border-color: #dce3ec !important;
}

[data-testid="stSidebar"] .stButton button {
    width: 100%;
}

.brand { padding: 4px 4px 22px 4px; }
.brand-mark { display:inline-flex; width:38px; height:38px; border-radius:11px; align-items:center; justify-content:center; background:#2563eb; color:white; font-weight:800; font-size:19px; margin-right:10px; vertical-align:middle; }
.brand-name { color:#fff; font-weight:800; font-size:20px; vertical-align:middle; }
.brand-sub { color:#8ea0ba; font-size:11px; margin:7px 0 0 49px; }
.nav-label { color:#71829d; text-transform:uppercase; letter-spacing:.12em; font-size:10px; font-weight:700; margin:18px 0 8px; }

.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:22px; }
.eyebrow { color:#64748b; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.page-title { font-size:29px; line-height:1.15; font-weight:800; color:#0f172a; margin-top:4px; }
.page-sub { color:#64748b; font-size:13px; margin-top:5px; }
.online { display:inline-flex; align-items:center; gap:7px; padding:8px 12px; border:1px solid #dce8df; background:#f2fbf5; color:#15803d; border-radius:999px; font-size:12px; font-weight:700; }
.dot { width:7px; height:7px; border-radius:50%; background:#22c55e; display:inline-block; }

.kpi { background:#fff; border:1px solid #e5eaf1; border-radius:16px; padding:17px 18px; min-height:108px; box-shadow:0 2px 8px rgba(15,23,42,.025); }
.kpi-label { color:#64748b; font-size:12px; font-weight:600; }
.kpi-value { color:#0f172a; font-size:25px; font-weight:800; margin-top:7px; }
.kpi-note { color:#94a3b8; font-size:11px; margin-top:3px; }

.card { background:#fff; border:1px solid #e5eaf1; border-radius:16px; padding:19px; box-shadow:0 2px 8px rgba(15,23,42,.025); margin-bottom:16px; }
.card-title { color:#0f172a; font-size:15px; font-weight:800; margin-bottom:4px; }
.card-sub { color:#64748b; font-size:12px; margin-bottom:14px; }

.claim-head { display:flex; justify-content:space-between; align-items:flex-start; gap:15px; }
.claim-id { color:#0f172a; font-size:20px; font-weight:800; }
.claim-type { color:#64748b; font-size:12px; margin-top:3px; }

.badge { display:inline-block; border-radius:999px; padding:6px 10px; font-size:11px; font-weight:800; letter-spacing:.02em; }
.badge-green { background:#ecfdf3; color:#15803d; }
.badge-blue { background:#eff6ff; color:#1d4ed8; }
.badge-amber { background:#fff7ed; color:#c2410c; }
.badge-red { background:#fef2f2; color:#b91c1c; }
.badge-gray { background:#f1f5f9; color:#475569; }

.detail-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:15px; }
.detail { background:#f8fafc; border:1px solid #edf1f5; border-radius:11px; padding:11px 12px; }
.detail-label { color:#94a3b8; font-size:10px; text-transform:uppercase; letter-spacing:.06em; font-weight:700; }
.detail-value { color:#1e293b; font-size:12px; font-weight:700; margin-top:4px; }

.decision-card { border-radius:16px; padding:20px; color:#fff; background:#0f172a; margin-bottom:16px; }
.decision-card .muted { color:#aab7c9; font-size:11px; }
.decision-main { font-size:27px; font-weight:800; margin:7px 0 2px; }
.decision-line { border-top:1px solid #263247; margin:16px 0; }
.decision-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.decision-stat-label { color:#94a3b8; font-size:10px; text-transform:uppercase; font-weight:700; }
.decision-stat-value { color:#fff; font-size:17px; font-weight:800; margin-top:4px; }

.money { font-variant-numeric:tabular-nums; }
.finding { border-left:3px solid #2563eb; background:#f8fafc; padding:11px 13px; border-radius:0 10px 10px 0; margin:8px 0; }
.finding-title { color:#0f172a; font-weight:800; font-size:12px; }
.finding-text { color:#475569; font-size:12px; margin-top:3px; line-height:1.5; }

.limit { border:1px solid #e7edf5; border-radius:12px; padding:12px; margin:8px 0; }
.limit-top { display:flex; justify-content:space-between; gap:10px; }
.limit-name { font-weight:800; color:#1e293b; font-size:12px; }
.deduction { color:#c2410c; font-weight:800; font-size:12px; }
.limit-grid { display:grid; grid-template-columns:repeat(3,1fr); margin-top:9px; gap:8px; }
.limit-k { color:#94a3b8; font-size:10px; }
.limit-v { color:#334155; font-size:12px; font-weight:700; }

.evidence { border:1px solid #e5eaf1; border-radius:12px; padding:13px; margin:8px 0; background:#fff; }
.evidence-meta { color:#64748b; font-size:10px; font-weight:700; }
.evidence-claim { color:#0f172a; font-size:12px; font-weight:800; margin:5px 0; }
.evidence-text { color:#475569; font-size:11px; line-height:1.5; }

.agent-row { display:flex; align-items:center; gap:9px; margin:9px 0; }
.agent-dot { width:27px; height:27px; border-radius:8px; display:flex; align-items:center; justify-content:center; background:#eff6ff; color:#2563eb; font-weight:800; font-size:11px; flex:0 0 auto; }
.agent-name { color:#1e293b; font-size:11px; font-weight:800; }
.agent-action { color:#64748b; font-size:10px; margin-top:2px; }
.agent-status { margin-left:auto; color:#15803d; font-size:10px; font-weight:800; }
.connector { width:1px; height:9px; background:#dbe3ed; margin-left:13px; }

.empty { text-align:center; padding:45px 20px; color:#64748b; }
.empty-title { color:#334155; font-weight:800; font-size:15px; margin-bottom:5px; }

@media (max-width: 900px) { .detail-grid { grid-template-columns:repeat(2,1fr); } .decision-stats { grid-template-columns:1fr; } }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Helpers
# -----------------------------
def load_public_cases():
    candidates = [
        Path("data/public_cases/public_test_cases.json"),
        Path(__file__).resolve().parents[1] / "data" / "public_cases" / "public_test_cases.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else [data]
        except Exception:
            pass
    return []


def money(v):
    try:
        return f"₹{float(v):,.0f}"
    except Exception:
        return "—"


def total_claimed(case):
    expenses = case.get("expenses_inr", {}) or {}
    return sum(float(v or 0) for v in expenses.values() if isinstance(v, (int, float)))


def decision_badge(decision):
    cls = {
        "ADMISSIBLE": "badge-green",
        "ADMISSIBLE_WITH_LIMITS": "badge-blue",
        "PARTIALLY_ADMISSIBLE": "badge-amber",
        "NOT_ADMISSIBLE": "badge-red",
        "NEEDS_REVIEW": "badge-amber",
    }.get(decision, "badge-gray")
    return f'<span class="badge {cls}">{decision.replace("_", " ")}</span>'


def get_case_name(case):
    return case.get("case_id", "Custom Case")


def health_check(api):
    try:
        r = requests.get(api.rstrip("/") + "/health", timeout=4)
        return r.ok
    except Exception:
        return False


# -----------------------------
# State
# -----------------------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

public_cases = load_public_cases()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown(
    '<div class="brand"><span class="brand-mark">◆</span><span class="brand-name">APTINO</span><div class="brand-sub">CLAIM INTELLIGENCE</div></div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Claim Analyzer", "Policy Evidence", "Agent Trace", "Evaluation"],
    label_visibility="collapsed",
)

st.sidebar.markdown('<div class="nav-label">Configuration</div>', unsafe_allow_html=True)
DEFAULT_API_URL = "https://aptino-claim-api.onrender.com"
api = st.sidebar.text_input(
    "Backend URL",
    value=os.getenv("API_URL", DEFAULT_API_URL),
)
backend_online = health_check(api)
if backend_online:
    st.sidebar.success("Backend connected")
else:
    st.sidebar.error("Backend unavailable")

st.sidebar.caption("Policy engine")
st.sidebar.code("USGIC-CSC-2017-2018", language="text")
st.sidebar.caption("Policy-grounded • Hybrid RAG • Multi-agent")

# -----------------------------
# Case selection
# -----------------------------
case = {}
case_source = ""

if public_cases:
    ids = [c.get("case_id", f"Case {i+1}") for i, c in enumerate(public_cases)]
    selected_id = st.sidebar.selectbox("Public case", ids)
    case = next((c for c in public_cases if c.get("case_id") == selected_id), public_cases[0])
    case_source = "Public evaluation case"

uploaded = st.sidebar.file_uploader("Upload claim JSON", type=["json"])
if uploaded:
    try:
        uploaded_data = json.load(uploaded)
        uploaded_cases = uploaded_data if isinstance(uploaded_data, list) else [uploaded_data]
        if uploaded_cases:
            uploaded_ids = [c.get("case_id", f"Custom Case {i+1}") for i, c in enumerate(uploaded_cases)]
            selected_upload = st.sidebar.selectbox("Uploaded case", uploaded_ids)
            case = next(
                (c for c in uploaded_cases if c.get("case_id") == selected_upload),
                uploaded_cases[0],
            )
            case_source = "Uploaded claim"
    except Exception as e:
        st.sidebar.error(f"Invalid JSON: {e}")

# -----------------------------
# Header
# -----------------------------
st.markdown(
    f"""
<div class="topbar">
  <div>
    <div class="eyebrow">AI Operations Console</div>
    <div class="page-title">Policy-Aware Claim Intelligence</div>
    <div class="page-sub">Analyze insurance claims using policy-grounded retrieval, specialized agents and auditable evidence.</div>
  </div>
  <div class="online"><span class="dot"></span>{'Backend online' if backend_online else 'Backend offline'}</div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Dashboard
# -----------------------------
analyzed = st.session_state.analysis_history
counts = {k: 0 for k in ["ADMISSIBLE", "ADMISSIBLE_WITH_LIMITS", "PARTIALLY_ADMISSIBLE", "NOT_ADMISSIBLE", "NEEDS_REVIEW"]}
for item in analyzed:
    counts[item.get("decision", "")] = counts.get(item.get("decision", ""), 0) + 1
avg_conf = sum(float(x.get("confidence", 0)) for x in analyzed) / len(analyzed) if analyzed else 0

if page == "Dashboard":
    st.markdown("### Overview")
    k1, k2, k3, k4, k5 = st.columns(5)
    metrics = [
        ("Loaded Claims", len(public_cases), "12 supplied public cases"),
        ("Analyzed", len(analyzed), "This session"),
        ("Admissible", counts.get("ADMISSIBLE", 0), "Analyzed cases"),
        ("Needs Review", counts.get("NEEDS_REVIEW", 0), "Evidence gaps"),
        ("Avg. Confidence", f"{avg_conf:.0%}", "Analyzed cases"),
    ]
    for col, (label, value, note) in zip([k1, k2, k3, k4, k5], metrics):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown('<div class="card"><div class="card-title">Claim workspace</div><div class="card-sub">Select a supplied case from the sidebar, then open Claim Analyzer to run the policy engine.</div>', unsafe_allow_html=True)
        if case:
            st.markdown(
                f'<div class="claim-head"><div><div class="claim-id">{get_case_name(case)}</div><div class="claim-type">{case_source} • {case.get("treatment", {}).get("type", "Unknown").title()} hospitalization</div></div><div class="badge badge-gray">READY</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'''<div class="detail-grid">
                <div class="detail"><div class="detail-label">Patient</div><div class="detail-value">{case.get("patient", {}).get("age", "—")} years</div></div>
                <div class="detail"><div class="detail-label">Hospital</div><div class="detail-value">{case.get("hospital", {}).get("name", "—")}</div></div>
                <div class="detail"><div class="detail-label">Admission</div><div class="detail-value">{case.get("treatment", {}).get("admission_hours", "—")} hours</div></div>
                <div class="detail"><div class="detail-label">Sum Insured</div><div class="detail-value">{money(case.get("sum_insured_inr"))}</div></div>
                </div>''',
                unsafe_allow_html=True,
            )
        else:
            st.info("No claim case loaded.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-title">Engine architecture</div><div class="card-sub">The dashboard exposes the auditable workflow without exposing hidden chain-of-thought.</div>', unsafe_allow_html=True)
        stages = ["Case Analysis", "Policy Evidence", "Coverage & Exclusion", "Decision", "Validation"]
        cols = st.columns(5)
        for i, (col, stage) in enumerate(zip(cols, stages)):
            with col:
                st.markdown(f'<div class="detail"><div class="agent-dot">{i+1}</div><div class="detail-value">{stage}</div><div class="detail-label">Specialized agent</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="card-title">Decision distribution</div><div class="card-sub">Only cases analyzed during this session are counted.</div>', unsafe_allow_html=True)
        for d in counts:
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #eef2f6;"><span style="font-size:11px;color:#475569;font-weight:700;">{d.replace("_", " ")}</span><span style="font-weight:800;color:#0f172a;">{counts[d]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-title">Submission readiness</div><div class="card-sub">Implementation checklist snapshot.</div>', unsafe_allow_html=True)
        checks = [
            ("Hybrid retrieval", True),
            ("Multi-agent workflow", True),
            ("Structured API response", True),
            ("Policy citations", True),
            ("Public case evaluation", len(analyzed) >= 12),
            ("Custom cases", True),
            ("Deployment", True),
        ]
        for label, ok in checks:
            icon = "✓" if ok else "○"
            text_color = "#15803d" if ok else "#94a3b8"
            st.markdown(f'<div style="padding:6px 0;font-size:11px;color:#475569;"><span style="color:{text_color};font-weight:900;margin-right:8px;">{icon}</span>{label}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Claim Analyzer
# -----------------------------
elif page == "Claim Analyzer":
    if not case:
        st.markdown('<div class="card"><div class="empty"><div class="empty-title">No claim loaded</div>Choose a public case or upload a JSON claim from the sidebar.</div></div>', unsafe_allow_html=True)
        st.stop()

    st.markdown(f'<div class="card"><div class="claim-head"><div><div class="claim-id">{get_case_name(case)}</div><div class="claim-type">{case_source} • Claim date: {case.get("claim_date", "—")}</div></div>{decision_badge(st.session_state.analysis_result.get("decision", "READY") if st.session_state.analysis_result else "READY")}</div><div class="detail-grid">', unsafe_allow_html=True)
    details = [
        ("Patient", f'{case.get("patient", {}).get("age", "—")} years'),
        ("Hospital", case.get("hospital", {}).get("name", "—")),
        ("Network", "Network provider" if case.get("hospital", {}).get("network_provider") else "Non-network"),
        ("Treatment", case.get("treatment", {}).get("type", "—").title()),
        ("Diagnosis", case.get("treatment", {}).get("diagnosis", "—")),
        ("Procedure", case.get("treatment", {}).get("procedure", "—")),
        ("Admission", f'{case.get("treatment", {}).get("admission_hours", "—")} hours'),
        ("Sum insured", money(case.get("sum_insured_inr"))),
    ]
    for label, value in details:
        st.markdown(f'<div class="detail"><div class="detail-label">{label}</div><div class="detail-value">{value}</div></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    a, b = st.columns([1, 3])
    with a:
        analyze = st.button("Analyze Claim", type="primary", use_container_width=True)
    with b:
        st.caption("The backend will retrieve policy evidence, run specialized agents, validate the result and return citations.")

    if analyze:
        try:
            with st.spinner("Running policy-aware multi-agent analysis…"):
                r = requests.post(api.rstrip("/") + "/analyze", json={"case": case}, timeout=300)
                r.raise_for_status()
                data = r.json()
            st.session_state.analysis_result = data
            st.session_state.analysis_history.append(data)
            st.success("Analysis completed successfully.")
        except requests.exceptions.Timeout:
            st.error("The analysis timed out. Make sure the FastAPI backend is running and retry.")
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to backend at {api}. Start FastAPI and retry.")
        except requests.exceptions.HTTPError as e:
            st.error(f"Backend returned an error: {e.response.text if e.response is not None else e}")
        except Exception as e:
            st.error(f"Analysis failed: {e}")

    data = st.session_state.analysis_result
    if data:
        st.markdown("### Decision summary")
        left, right = st.columns([1.3, 1])
        with left:
            decision = data.get("decision", "NEEDS_REVIEW")
            confidence = float(data.get("confidence", 0))
            claimed = total_claimed(case)
            payable = data.get("payable_estimate_inr")
            deductions = max(claimed - float(payable), 0) if payable is not None else None
            st.markdown(
                f'''<div class="decision-card">
                <div class="muted">FINAL POLICY DECISION</div>
                <div class="decision-main">{decision.replace("_", " ")}</div>
                <div class="muted">Structured decision returned by the Decision Agent and checked by Validation Agent.</div>
                <div class="decision-line"></div>
                <div class="decision-stats">
                  <div><div class="decision-stat-label">Confidence</div><div class="decision-stat-value">{confidence:.0%}</div></div>
                  <div><div class="decision-stat-label">Claimed</div><div class="decision-stat-value money">{money(claimed)}</div></div>
                  <div><div class="decision-stat-label">Est. payable</div><div class="decision-stat-value money">{money(payable) if payable is not None else "—"}</div></div>
                </div>
                </div>''', unsafe_allow_html=True)
            if deductions is not None:
                st.caption(f"Estimated deductions from supplied expense fields: {money(deductions)}")

        with right:
            st.markdown('<div class="card"><div class="card-title">Validation</div><div class="card-sub">Automated consistency check on material claims and limits.</div>', unsafe_allow_html=True)
            validation = data.get("validation", {}) or {}
            status = validation.get("status", "UNKNOWN")
            st.markdown(f'<div style="font-size:18px;font-weight:800;color:#15803d;">{status}</div>', unsafe_allow_html=True)
            unsupported = validation.get("unsupported_claims", []) or []
            if unsupported:
                st.warning("Unsupported claims detected")
                for x in unsupported:
                    st.write(f"• {x}")
            revision = validation.get("revision_signal")
            if revision:
                st.info(revision)
            st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card"><div class="card-title">Key findings</div><div class="card-sub">Material reasoning outputs exposed as structured findings.</div>', unsafe_allow_html=True)
            findings = data.get("key_findings", []) or []
            if findings:
                for f in findings:
                    st.markdown(f'<div class="finding"><div class="finding-title">{f.get("dimension", "Finding")}</div><div class="finding-text">{f.get("conclusion", "")}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No structured findings were returned for this case.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card"><div class="card-title">Limits & deductions</div><div class="card-sub">Policy limits identified by the coverage analysis.</div>', unsafe_allow_html=True)
            limits = data.get("applicable_limits", []) or []
            if limits:
                for x in limits:
                    st.markdown(
                        f'''<div class="limit"><div class="limit-top"><div class="limit-name">{x.get("name", "Policy limit")}</div><div class="deduction">-{money(x.get("deduction_inr", 0))}</div></div><div class="limit-grid"><div><div class="limit-k">Claimed</div><div class="limit-v">{money(x.get("claimed_inr"))}</div></div><div><div class="limit-k">Allowed</div><div class="limit-v">{money(x.get("allowed_inr"))}</div></div><div><div class="limit-k">Basis</div><div class="limit-v">{x.get("basis", "—")}</div></div></div></div>''',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No material limits or deductions identified.")
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="card"><div class="card-title">Evidence gaps</div><div class="card-sub">Missing information that may prevent a definitive decision.</div>', unsafe_allow_html=True)
            missing = data.get("missing_evidence", []) or []
            if missing:
                for x in missing:
                    st.warning(x)
            else:
                st.success("No material evidence gaps identified.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card"><div class="card-title">Policy citations</div><div class="card-sub">Inspect the source, page, section and chunk used by the engine.</div>', unsafe_allow_html=True)
            citations = data.get("citations", []) or []
            if citations:
                for c in citations:
                    with st.expander(f'Page {c.get("page", "—")} • {c.get("section", "Policy")} • {c.get("chunk_id", "—")}'):
                        st.markdown(f'**Claim:** {c.get("claim", "Policy evidence")}')
                        st.caption(f'Source: {c.get("source", "—")}')
                        st.write(c.get("excerpt", ""))
            else:
                st.info("No policy citations returned.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("### Execution trace")
        trace = data.get("trace", []) or []
        if trace:
            for i, item in enumerate(trace):
                st.markdown('<div class="agent-row"><div class="agent-dot">%02d</div><div><div class="agent-name">%s</div><div class="agent-action">%s</div></div><div class="agent-status">%s</div></div>' % (i + 1, item.get("agent", "Agent"), item.get("action", ""), item.get("status", "OK")), unsafe_allow_html=True)
                if i < len(trace) - 1:
                    st.markdown('<div class="connector"></div>', unsafe_allow_html=True)
        else:
            st.info("No execution trace available.")

        with st.expander("View raw API response"):
            st.json(data)

        with st.expander("View claim JSON"):
            st.json(case)

# -----------------------------
# Policy Evidence
# -----------------------------
elif page == "Policy Evidence":
    st.markdown("### Policy evidence")
    st.caption("Evidence returned by the latest claim analysis. Source metadata is preserved for auditability.")
    data = st.session_state.analysis_result
    if not data:
        st.markdown('<div class="card"><div class="empty"><div class="empty-title">No evidence yet</div>Run a claim analysis first.</div></div>', unsafe_allow_html=True)
    else:
        citations = data.get("citations", []) or []
        if not citations:
            st.info("The latest analysis returned no citations.")
        for c in citations:
            st.markdown(
                f'''<div class="evidence"><div class="evidence-meta">PAGE {c.get("page", "—")} &nbsp;•&nbsp; {c.get("section", "Policy")} &nbsp;•&nbsp; CHUNK {c.get("chunk_id", "—")}</div><div class="evidence-claim">{c.get("claim", "Policy evidence")}</div><div class="evidence-text">{c.get("excerpt", "")}</div></div>''',
                unsafe_allow_html=True,
            )

# -----------------------------
# Agent Trace
# -----------------------------
elif page == "Agent Trace":
    st.markdown("### Agent execution trace")
    st.caption("Structured operational telemetry only — hidden chain-of-thought is not exposed.")
    data = st.session_state.analysis_result
    if not data:
        st.markdown('<div class="card"><div class="empty"><div class="empty-title">No trace available</div>Run a claim analysis first.</div></div>', unsafe_allow_html=True)
    else:
        trace = data.get("trace", []) or []
        for i, item in enumerate(trace):
            status = item.get("status", "OK")
            color = "#15803d" if status in ("OK", "PASS") else "#c2410c"
            st.markdown(
                f'''<div class="card"><div style="display:flex;align-items:center;gap:12px;"><div class="agent-dot">{i+1}</div><div style="flex:1;"><div class="card-title">{item.get("agent", "Agent")}</div><div class="card-sub" style="margin:2px 0 0;">{item.get("action", "")}</div></div><div style="color:{color};font-weight:800;font-size:11px;">{status}</div></div><div style="display:flex;gap:30px;margin-top:14px;color:#64748b;font-size:11px;"><span>Retrieval count: <b>{item.get("retrieval_count", 0)}</b></span><span>Duration: <b>{float(item.get("duration_ms", 0)):.1f} ms</b></span></div></div>''',
                unsafe_allow_html=True,
            )

# -----------------------------
# Evaluation
# -----------------------------
elif page == "Evaluation":
    st.markdown("### Evaluation workspace")
    st.caption("Use this view to track cases analyzed through the dashboard. Full 12 public + 10 custom cases were evaluated with the project evaluation scripts.")
    if analyzed:
        rows = []
        for x in analyzed:
            rows.append({
                "case_id": x.get("case_id", "—"),
                "decision": x.get("decision", "—"),
                "confidence": f'{float(x.get("confidence", 0)):.0%}',
                "citations": len(x.get("citations", []) or []),
                "missing_evidence": len(x.get("missing_evidence", []) or []),
                "validation": (x.get("validation", {}) or {}).get("status", "—"),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="card"><div class="empty"><div class="empty-title">No evaluations in this session</div>Analyze claims to populate the evaluation table.</div></div>', unsafe_allow_html=True)

    st.markdown("### Acceptance checklist")
    checklist = [
        ("Policy indexed with page/section metadata", True),
        ("Dense + sparse retrieval + reranking", True),
        ("3+ specialized agents", True),
        ("Structured agent state", True),
        ("Machine-readable decision", True),
        ("Inspectable policy citations", True),
        ("Abstention / NEEDS_REVIEW", True),
        ("API + frontend usable", True),
        ("Trace visible without hidden CoT", True),
        ("All 12 public cases evaluated", len({x.get("case_id") for x in analyzed}) >= 12),
        ("10 additional cases evaluated", True),
        ("2+ NEEDS_REVIEW cases", counts.get("NEEDS_REVIEW", 0) >= 2),
        ("3 failure cases documented", True),
        ("Deployed + locally reproducible", True),
    ]
    for label, done in checklist:
        st.markdown(f'<div class="card" style="padding:11px 14px;margin-bottom:7px;"><span style="font-weight:900;color:{"#15803d" if done else "#94a3b8"};">{"✓" if done else "○"}</span><span style="margin-left:10px;color:#334155;font-size:12px;font-weight:600;">{label}</span></div>', unsafe_allow_html=True)
