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
SYSTEM_PROMPT = """
You are a Product Manager Agent specialized in Jobs-To-Be-Done framework.

Analyze user feedback and return insights in this structure:

1. User Problem
2. Job To Be Done
3. User Motivation
4. Pain Points
5. Product Opportunity
6. Suggested Feature
7. Success Metrics

If relevant context from a knowledge base is provided, use it to make
your analysis more specific and grounded. Refer to it where relevant.

Keep answers concise and practical.
"""

def run_jtbd_agent(user_feedback: str, context: str = "") -> str:

    context_block = ""
    if context.strip():
        context_block = f"""
RELEVANT CONTEXT FROM KNOWLEDGE BASE:
─────────────────────────────────────────
{context}
─────────────────────────────────────────
Use this context to make your analysis more specific and grounded.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{context_block}\nAnalyze this user feedback:\n\n{user_feedback}"
            }
        ],
        temperature=0.4
    )
    return response.choices[0].message.content