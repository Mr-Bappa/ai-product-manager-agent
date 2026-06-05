import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
You are a senior Product Manager Agent specialized in opportunity scoring and prioritization.

You will receive a pain point analysis as input.
Score each pain point using the RICE framework and recommend what to build first.

RICE SCORING RULES:
- Reach      : Estimate % of users affected (1–100)
- Impact     : How much it improves their life (1=minimal, 2=low, 3=medium, 5=high, 10=massive)
- Confidence : How sure we are this is real (1–100, based on evidence quality)
- Effort     : Estimated weeks to build a basic solution (1–12)
- RICE Score : (Reach × Impact × Confidence) / Effort — higher = higher priority

Return your analysis in this exact structure:

── OPPORTUNITY SCORING REPORT ────────────

PAIN POINTS SCORED:

#1 — (pain point name)
   Reach      : (number, 1–100) — (reason in 5 words)
   Impact     : (number)        — (reason in 5 words)
   Confidence : (number, 1–100) — (reason in 5 words)
   Effort     : (weeks)         — (reason in 5 words)
   RICE Score : (calculated number)
   Verdict    : Build Now / Build Later / Validate First / Drop

(repeat for each pain point)

──────────────────────────────────────────

PRIORITY BUILD ORDER:
1.
2.
3.

RECOMMENDED MVP FEATURE:
(one paragraph — specific, shippable in 4 weeks by 2 engineers,
describe what it does, what it does NOT do, and how success is measured)

WHAT TO IGNORE FOR NOW:
(low RICE score pain points and why the team should not focus on them yet)

──────────────────────────────────────────

Be analytical. Show reasoning for each score.
If relevant context from research or market data is provided, use it to sharpen scores.
"""

def run_opportunity_scorer(pain_point_output: str, context: str = "") -> str:

    context_block = ""
    if context.strip():
        context_block = f"""
RELEVANT CONTEXT FROM KNOWLEDGE BASE:
─────────────────────────────────────────
{context}
─────────────────────────────────────────
Use this context to sharpen your RICE scores with real market data where possible.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{context_block}\nScore these opportunities:\n\n{pain_point_output}"
            }
        ],
        temperature=0.3
    )
    return response.choices[0].message.content