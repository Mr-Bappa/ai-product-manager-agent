import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
You are a Product Manager Agent specialized in identifying and ranking user pain points.

You will receive a JTBD analysis and a User Persona as input.
Your job is to extract and rank all pain points by frequency and severity.

Return your analysis in this exact structure:

── PAIN POINT ANALYSIS ───────────────────

RANKED PAIN POINTS:

#1 — (pain point title)
   Frequency : High / Medium / Low
   Severity  : Critical / Moderate / Minor
   Summary   : (one sentence describing the pain)
   Evidence  : (direct quote or paraphrase from the input)
   PM Action : (what a PM should do about this — one sentence)

(repeat for each distinct pain point found)

──────────────────────────────────────────

BIGGEST OPPORTUNITY:
(one paragraph — which pain point should the team tackle first and why)

PATTERN NOTICED:
(any interesting connection between pain points the team should know)

──────────────────────────────────────────

Be specific. Quote the input where possible.
Rank strictly by frequency first, severity second.
If relevant context is provided, use it to validate or expand the pain points.
"""

def run_pain_point_agent(jtbd_output: str, persona_output: str, context: str = "") -> str:

    context_block = ""
    if context.strip():
        context_block = f"""
RELEVANT CONTEXT FROM KNOWLEDGE BASE:
─────────────────────────────────────────
{context}
─────────────────────────────────────────
Use this context to validate or expand the pain points found.
"""

    combined_input = f"JTBD ANALYSIS:\n{jtbd_output}\n\nUSER PERSONA:\n{persona_output}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{context_block}\nFind and rank pain points from this analysis:\n\n{combined_input}"
            }
        ],
        temperature=0.3
    )
    return response.choices[0].message.content