import os
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
load_dotenv()

client = OpenAI(
    api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
You are a Product Manager Agent specialized in building User Personas.

You will receive a JTBD analysis as input.
Your job is to construct a realistic, detailed user persona based on that analysis.

Return the persona in this exact structure:

── PERSONA CARD ──────────────────────────

NAME: (a realistic first name)
ROLE: (their job title or life role)
AGE RANGE: (e.g. 28–35)
TECH COMFORT: (Low / Medium / High)

ABOUT:
(2–3 sentences describing who this person is and their daily life)

GOALS:
- (what they want to achieve, 3 bullet points)

FRUSTRATIONS:
- (what blocks or annoys them, 3 bullet points)

DAILY BEHAVIORS:
- (how they currently work or live, 3 bullet points)

THEIR WORDS:
"(a realistic quote this person might say about their problem)"

BEST CHANNEL TO REACH THEM:
(e.g. email, push notification, Slack, SMS)

──────────────────────────────────────────

Be specific and realistic. Avoid generic statements.
Base everything strictly on the JTBD input given.
If relevant context is provided, use it to add realism to the persona.
"""

def run_persona_agent(jtbd_output: str, context: str = "") -> str:

    context_block = ""
    if context.strip():
        context_block = f"""
RELEVANT CONTEXT FROM KNOWLEDGE BASE:
─────────────────────────────────────────
{context}
─────────────────────────────────────────
Use this context to make the persona more realistic and specific.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{context_block}\nBuild a user persona based on this JTBD analysis:\n\n{jtbd_output}"
            }
        ],
        temperature=0.5
    )
    return response.choices[0].message.content