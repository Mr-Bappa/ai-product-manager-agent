import time
import streamlit as st
from dotenv import load_dotenv

from agents.jtbd_agent import run_jtbd_agent
from agents.persona_agent import run_persona_agent
from agents.pain_point_agent import run_pain_point_agent
from agents.opportunity_scorer_agent import run_opportunity_scorer
from agents.prd_writer_agent import run_prd_writer
from agents.chat_agent import chat_with_report
from utils.docx_exporter import build_prd_docx


load_dotenv()

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Product Manager",
    page_icon="🧠",
    layout="wide"
)

# ── CSS ────────────────────────────────────────────────────────────
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

    .metric-box {
        background: #1e1e2e;
        border: 1px solid #3a3a5c;
        border-radius: 8px;
        padding: 1rem;
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

    .chat-section {
        background: #1e1e2e;
        border: 1px solid #3a3a5c;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
    }

    .chat-message-user {
        background: #2d2d4e;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        color: #e2e8f0;
        font-size: 0.9rem;
    }

    .chat-message-agent {
        background: #13131f;
        border: 1px solid #2a2a3e;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        color: #e2e8f0;
        font-size: 0.9rem;
        white-space: pre-wrap;
    }

    .chat-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
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
        Paste user feedback → 5 agents analyze it → full PM report + chat
    </p>
</div>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────
defaults = {
    "results": {},
    "pipeline_done": False,
    "feedback_submitted": "",
    "chat_history": [],           # list of {"role": "user/assistant", "content": "..."}
    "chat_agent_history": [],     # full history sent to the API (includes system prompt)
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Layout ─────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.6], gap="large")


# ── LEFT: Input ────────────────────────────────────────────────────
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

    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics
    m1, m2, m3 = st.columns(3)
    agents_done = len(st.session_state.results)

    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{agents_done}/5</div>
            <div class="metric-label">Agents done</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        word_count = sum(len(v.split()) for v in st.session_state.results.values())
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

    # Downloads
    if st.session_state.pipeline_done:
        st.markdown("<br>", unsafe_allow_html=True)

        full_report = f"AI PRODUCT MANAGER REPORT\n{'='*50}\n\n"
        full_report += f"ORIGINAL FEEDBACK:\n{st.session_state.feedback_submitted}\n\n"
        for section, content in st.session_state.results.items():
            full_report += f"{'='*50}\n{section}\n{'='*50}\n{content}\n\n"

        st.download_button(
            label="⬇ Download Report (.txt)",
            data=full_report,
            file_name="pm_report.txt",
            mime="text/plain"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if "AGENT 5 — PRD" in st.session_state.results:
            try:
                docx_bytes = build_prd_docx(
                    original_feedback  = st.session_state.feedback_submitted,
                    jtbd_output        = st.session_state.results.get("AGENT 1 — JTBD ANALYSIS", ""),
                    persona_output     = st.session_state.results.get("AGENT 2 — USER PERSONA", ""),
                    pain_point_output  = st.session_state.results.get("AGENT 3 — PAIN POINT ANALYSIS", ""),
                    opportunity_output = st.session_state.results.get("AGENT 4 — OPPORTUNITY SCORING", ""),
                    prd_output         = st.session_state.results.get("AGENT 5 — PRD", "")
                )
                st.download_button(
                    label     = "⬇ Download PRD (.docx)",
                    data      = docx_bytes,
                    file_name = "pm_report.docx",
                    mime      = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Could not generate Word file: {e}")


# ── RIGHT: Agent outputs ───────────────────────────────────────────
with right_col:
    st.markdown("### Agent Outputs")

    agents = [
        ("1", "JTBD Analysis",               "AGENT 1 — JTBD ANALYSIS"),
        ("2", "User Persona",                 "AGENT 2 — USER PERSONA"),
        ("3", "Pain Point Analysis",          "AGENT 3 — PAIN POINT ANALYSIS"),
        ("4", "Opportunity Scoring",          "AGENT 4 — OPPORTUNITY SCORING"),
        ("5", "PRD",                          "AGENT 5 — PRD"),
    ]

    for num, label, key in agents:
        has_result   = key in st.session_state.results
        status_class = "status-done"    if has_result else "status-waiting"
        status_text  = "✓ Complete"     if has_result else "Waiting..."

        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-header">
                <span style="color:#818cf8;">Agent {num}</span>
                &nbsp;·&nbsp;
                {label}
                <span class="{status_class}" style="float:right;">{status_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if has_result:
            st.markdown(
                f'<div class="output-box">{st.session_state.results[key]}</div>',
                unsafe_allow_html=True
            )


# ── Pipeline execution ─────────────────────────────────────────────
if run_button:
    if not user_feedback.strip():
        st.warning("Please paste some user feedback first.")
    else:
        # Reset everything for fresh run
        st.session_state.results           = {}
        st.session_state.pipeline_done     = False
        st.session_state.feedback_submitted = user_feedback
        st.session_state.chat_history      = []
        st.session_state.chat_agent_history = []

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
                jtbd_output        = jtbd_out,
                persona_output     = persona_out,
                pain_point_output  = pain_out,
                opportunity_output = score_out
            )
            st.session_state.results["AGENT 5 — PRD"] = prd_out

        st.session_state.pipeline_done = True
        st.rerun()


# ── Chat interface ─────────────────────────────────────────────────
# Only show after pipeline has run
if st.session_state.pipeline_done:

    st.markdown("---")
    st.markdown("""
    <div class="chat-section">
        <h3 style="color:#818cf8; margin:0 0 0.3rem;">
            💬 Chat with your PM Report
        </h3>
        <p style="color:#6b7280; font-size:0.85rem; margin:0 0 1rem;">
            Ask anything about the analysis — rewrites, sprint plans, pitch emails, next steps.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show existing chat messages
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-label" style="color:#818cf8;">You</div>
            <div class="chat-message-user">{msg["content"]}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-label" style="color:#10b981;">PM Agent</div>
            <div class="chat-message-agent">{msg["content"]}</div>
            """, unsafe_allow_html=True)

    # Suggested prompts — shown only when chat is empty
    if not st.session_state.chat_history:
        st.markdown(
            "<p style='color:#6b7280; font-size:0.8rem; margin:1rem 0 0.5rem;'>"
            "Try asking:</p>",
            unsafe_allow_html=True
        )

        suggestions = [
            "What should the team build in the first 2 weeks?",
            "Write a one paragraph investor pitch for this product",
            "Rewrite the PRD in a more technical tone for engineers",
            "What is the biggest risk in this product plan?",
            "Write 3 interview questions to validate this persona",
        ]

        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggestion_{i}"):
                    # Treat button click as a chat message
                    report_context = {
                        "feedback":      st.session_state.feedback_submitted,
                        "jtbd":          st.session_state.results.get("AGENT 1 — JTBD ANALYSIS", ""),
                        "persona":       st.session_state.results.get("AGENT 2 — USER PERSONA", ""),
                        "pain_points":   st.session_state.results.get("AGENT 3 — PAIN POINT ANALYSIS", ""),
                        "opportunities": st.session_state.results.get("AGENT 4 — OPPORTUNITY SCORING", ""),
                        "prd":           st.session_state.results.get("AGENT 5 — PRD", "")
                    }

                    with st.spinner("Thinking..."):
                        reply, updated_history = chat_with_report(
                            user_message         = suggestion,
                            conversation_history = st.session_state.chat_agent_history,
                            report_context       = report_context
                        )

                    st.session_state.chat_agent_history = updated_history
                    st.session_state.chat_history.append({"role": "user",      "content": suggestion})
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()

    # Chat input box
    st.markdown("<br>", unsafe_allow_html=True)
    chat_input = st.text_area(
        label="chat_input",
        label_visibility="collapsed",
        placeholder="Ask anything about this report...",
        height=80,
        key="chat_input_box"
    )

    send_button = st.button("Send →", key="send_chat")

    if send_button and chat_input.strip():
        report_context = {
            "feedback":      st.session_state.feedback_submitted,
            "jtbd":          st.session_state.results.get("AGENT 1 — JTBD ANALYSIS", ""),
            "persona":       st.session_state.results.get("AGENT 2 — USER PERSONA", ""),
            "pain_points":   st.session_state.results.get("AGENT 3 — PAIN POINT ANALYSIS", ""),
            "opportunities": st.session_state.results.get("AGENT 4 — OPPORTUNITY SCORING", ""),
            "prd":           st.session_state.results.get("AGENT 5 — PRD", "")
        }

        with st.spinner("Thinking..."):
            reply, updated_history = chat_with_report(
                user_message         = chat_input.strip(),
                conversation_history = st.session_state.chat_agent_history,
                report_context       = report_context
            )

        st.session_state.chat_agent_history = updated_history
        st.session_state.chat_history.append({"role": "user",      "content": chat_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()