import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
load_dotenv()

def get_groq_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=get_groq_api_key() ,
    base_url="https://api.groq.com/openai/v1"
)


def build_system_prompt(
    feedback: str,
    jtbd: str,
    persona: str,
    pain_points: str,
    opportunities: str,
    prd: str
) -> str:
    """
    Builds a system prompt that contains the full report as context.
    The chat agent knows everything the pipeline produced.
    """
    return f"""
You are an expert Product Manager assistant.

You have just completed a full PM analysis for the following user feedback:

ORIGINAL FEEDBACK:
{feedback}

You produced these outputs:

── JTBD ANALYSIS ──
{jtbd}

── USER PERSONA ──
{persona}

── PAIN POINT ANALYSIS ──
{pain_points}

── OPPORTUNITY SCORING ──
{opportunities}

── PRODUCT REQUIREMENTS DOCUMENT ──
{prd}

Your job is to answer any follow-up questions about this analysis.
You can:
- Clarify any part of the report
- Rewrite sections in a different format or tone
- Generate new content based on the analysis (emails, pitch decks, sprint plans)
- Answer strategic questions about the product
- Suggest next steps

Always base your answers on the analysis above.
Be concise, direct, and practical.
If asked to rewrite something, do it fully — do not just describe what you would write.
"""


def chat_with_report(
    user_message: str,
    conversation_history: list,
    report_context: dict
) -> tuple:
    """
    Takes a user message and conversation history.
    Returns the agent reply and updated conversation history.

    On first call, builds system prompt from full report.
    On subsequent calls, just appends to history.
    """

    # First message — initialize with system prompt
    if not conversation_history:
        system_prompt = build_system_prompt(
            feedback     = report_context.get("feedback", ""),
            jtbd         = report_context.get("jtbd", ""),
            persona      = report_context.get("persona", ""),
            pain_points  = report_context.get("pain_points", ""),
            opportunities= report_context.get("opportunities", ""),
            prd          = report_context.get("prd", "")
        )
        conversation_history = [
            {"role": "system", "content": system_prompt}
        ]

    # Add user message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history,
        temperature=0.5
    )

    reply = response.choices[0].message.content

    # Save reply to history
    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return reply, conversation_history