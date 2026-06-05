import time
import streamlit as st
from dotenv import load_dotenv

from agents.jtbd_agent import run_jtbd_agent
from agents.persona_agent import run_persona_agent
from agents.pain_point_agent import run_pain_point_agent
from agents.opportunity_scorer_agent import run_opportunity_scorer
from agents.prd_writer_agent import run_prd_writer

load_dotenv()

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Product Manager",
    page_icon="🧠",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }

    .title-block {
        background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
        border: 1px solid #3a3a5c;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .agent-card {
        background: #1e1e2e;
        border: 1px solid #3a3a5c;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }

    .agent-header {
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .status-running { color: #f59e0b; }
    .status-done    { color: #10b981; }
    .status-waiting { color: #6b7280; }

    .output-box {
        background: #13131f;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        white-space: pre-wrap;
        color: #e2e8f0;
        max-height: 400px;
        overflow-y: auto;
    }

    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .metric-box {
        background: #1e1e2e;
        border: 1px solid #3a3a5c;
        border-radius: 8px;
        padding: 1rem;
        flex: 1;
        text-align: center;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #818cf8;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stTextArea"] textarea {
        background: #1e1e2e !important;
        border: 1px solid #3a3a5c !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stButton"] button {
        background: #4f46e5 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        font-size: 1rem !important;
    }

    div[data-testid="stButton"] button:hover {
        background: #4338ca !important;
    }

    div[data-testid="stDownloadButton"] button {
        background: #065f46 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100% !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────
st.markdown("""
<div class="title-block">
    <h1 style="color:#818cf8; margin:0; font-size:2rem;">🧠 AI Product Manager</h1>
    <p style="color:#6b7280; margin:0.5rem 0 0;">
        Paste user feedback → 4 agents analyze it → full PM report in seconds
    </p>
</div>
""", unsafe_allow_html=True)


# ── Session state setup ────────────────────────────────────────────
# Session state persists values between Streamlit reruns
if "results" not in st.session_state:
    st.session_state.results = {}

if "pipeline_done" not in st.session_state:
    st.session_state.pipeline_done = False

if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = ""


# ── Layout: two columns ────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.6], gap="large")


# ── LEFT COLUMN: Input ─────────────────────────────────────────────
with left_col:
    st.markdown("### Paste User Feedback")
    st.markdown(
        "<p style='color:#6b7280; font-size:0.85rem; margin-top:-0.5rem;'>"
        "Interview transcript, survey response, support ticket — anything works."
        "</p>",
        unsafe_allow_html=True
    )

    user_feedback = st.text_area(
        label="feedback_input",
        label_visibility="collapsed",
        placeholder=(
            "Example:\n\n"
            "I run a small design agency. Every week I lose track of what "
            "I promised clients. I use email, Notion, and WhatsApp but nothing "
            "talks to each other. By Thursday I'm scrambling. I just want "
            "something that tells me every morning what I owe people today."
        ),
        height=260
    )

    run_button = st.button("Run Full PM Analysis →")

    # Metrics row — updates after pipeline runs
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)

    agents_done = len(st.session_state.results)

    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{agents_done}/5</div>
            <div class="metric-label">Agents done</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        word_count = sum(
            len(v.split())
            for v in st.session_state.results.values()
        )
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{word_count}</div>
            <div class="metric-label">Words generated</div>
        </div>""", unsafe_allow_html=True)

    with m3:
        status = "✅ Done" if st.session_state.pipeline_done else "⏳ Waiting"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="font-size:1.2rem;">{status}</div>
            <div class="metric-label">Pipeline status</div>
        </div>""", unsafe_allow_html=True)

    # Download button — appears after pipeline runs
    if st.session_state.pipeline_done:
        st.markdown("<br>", unsafe_allow_html=True)

        full_report = f"AI PRODUCT MANAGER REPORT\n{'='*50}\n\n"
        full_report += f"ORIGINAL FEEDBACK:\n{st.session_state.feedback_submitted}\n\n"
        for section, content in st.session_state.results.items():
            full_report += f"{'='*50}\n{section}\n{'='*50}\n{content}\n\n"

        st.download_button(
            label="⬇ Download Full Report (.txt)",
            data=full_report,
            file_name="pm_report.txt",
            mime="text/plain"
        )


# ── RIGHT COLUMN: Agent outputs ────────────────────────────────────
with right_col:
    st.markdown("### Agent Outputs")

    agents = [
        ("1", "JTBD Analysis",        "AGENT 1 — JTBD ANALYSIS"),
        ("2", "User Persona",          "AGENT 2 — USER PERSONA"),
        ("3", "Pain Point Analysis",   "AGENT 3 — PAIN POINT ANALYSIS"),
        ("4", "Opportunity Scoring",   "AGENT 4 — OPPORTUNITY SCORING"),
        ("5", "PRD",                   "AGENT 5 — PRD"),  
    ]

    # Placeholders — we'll fill these during the pipeline run
    placeholders = {}
    for num, label, key in agents:
        has_result = key in st.session_state.results

        status_class = "status-done" if has_result else "status-waiting"
        status_text  = "✓ Complete"  if has_result else "Waiting..."

        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-header">
                <span style="color:#818cf8;">Agent {num}</span>
                &nbsp;·&nbsp;
                {label}
                &nbsp;&nbsp;
                <span class="{status_class}" style="float:right;">{status_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if has_result:
            st.markdown(
                f'<div class="output-box">{st.session_state.results[key]}</div>',
                unsafe_allow_html=True
            )
        else:
            placeholders[key] = st.empty()


# ── Pipeline execution ─────────────────────────────────────────────
if run_button:

    if not user_feedback.strip():
        st.warning("Please paste some user feedback first.")

    else:
        # Reset previous results
        st.session_state.results = {}
        st.session_state.pipeline_done = False
        st.session_state.feedback_submitted = user_feedback

        # Run agents one by one — page updates live after each one
        with st.spinner("Running Agent 1 — JTBD Analysis..."):
            time.sleep(0.5)
            jtbd_out = run_jtbd_agent(user_feedback)
            st.session_state.results["AGENT 1 — JTBD ANALYSIS"] = jtbd_out

        with st.spinner("Running Agent 2 — User Persona..."):
            time.sleep(0.5)
            persona_out = run_persona_agent(jtbd_out)
            st.session_state.results["AGENT 2 — USER PERSONA"] = persona_out

        with st.spinner("Running Agent 3 — Pain Point Analysis..."):
            time.sleep(0.5)
            pain_out = run_pain_point_agent(jtbd_out, persona_out)
            st.session_state.results["AGENT 3 — PAIN POINT ANALYSIS"] = pain_out

        with st.spinner("Running Agent 4 — Opportunity Scoring..."):
            time.sleep(0.5)
            score_out = run_opportunity_scorer(pain_out)
            st.session_state.results["AGENT 4 — OPPORTUNITY SCORING"] = score_out

        with st.spinner("Running Agent 5 — PRD Writer..."):
            time.sleep(0.5)
            prd_out = run_prd_writer(
                jtbd_output=jtbd_out,
                persona_output=persona_out,
                pain_point_output=pain_out,
                opportunity_output=score_out,
                context=""
            )
            st.session_state.results["AGENT 5 — PRD"] = prd_out

        st.session_state.pipeline_done = True
        st.rerun()  # refresh page to show all results cleanly