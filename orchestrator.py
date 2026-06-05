import os
import time
from dotenv import load_dotenv

from agents.jtbd_agent import run_jtbd_agent
from agents.persona_agent import run_persona_agent
from agents.pain_point_agent import run_pain_point_agent
from agents.opportunity_scorer_agent import run_opportunity_scorer
from agents.prd_writer_agent import run_prd_writer          # ← new

load_dotenv()


def get_rag_contexts(user_feedback: str) -> dict:
    try:
        from rag.retriever import retrieve_for_agents
        contexts = retrieve_for_agents(user_feedback)
        has_context = any(v.strip() for v in contexts.values())
        if has_context:
            print("[✓ Relevant context found — agents will use your documents]")
        else:
            print("[No matching documents found — running without RAG context]")
        return contexts
    except Exception:
        print("[RAG not set up — running without knowledge base]")
        return {
            "jtbd": "",
            "persona": "",
            "pain_points": "",
            "opportunities": "",
            "prd": ""                                        # ← new
        }


def print_section(title: str, content: str):
    print("\n" + "█" * 50)
    print(f"  {title}")
    print("█" * 50)
    print(content)


def save_report(feedback: str, results: dict, filename: str = "pm_report.txt"):
    with open(filename, "w", encoding ="utf-8") as f:
        f.write("AI PRODUCT MANAGER REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write("ORIGINAL FEEDBACK:\n")
        f.write(feedback + "\n\n")
        for section, content in results.items():
            f.write("=" * 50 + "\n")
            f.write(f"{section}\n")
            f.write("=" * 50 + "\n")
            f.write(content + "\n\n")
    print(f"\n[Report saved to pm_report.txt]")


def run_pipeline(user_feedback: str, save: bool = True) -> dict:
    results = {}

    # RAG context
    print("\n[0/5] Searching knowledge base...")
    contexts = get_rag_contexts(user_feedback)

    # Agent 1
    print("\n[1/5] Running JTBD Agent...")
    time.sleep(0.5)
    jtbd_out = run_jtbd_agent(user_feedback, context=contexts["jtbd"])
    results["AGENT 1 — JTBD ANALYSIS"] = jtbd_out
    print_section("AGENT 1 — JTBD ANALYSIS", jtbd_out)

    # Agent 2
    print("\n[2/5] Running Persona Agent...")
    time.sleep(0.5)
    persona_out = run_persona_agent(jtbd_out, context=contexts["persona"])
    results["AGENT 2 — USER PERSONA"] = persona_out
    print_section("AGENT 2 — USER PERSONA", persona_out)

    # Agent 3
    print("\n[3/5] Running Pain Point Agent...")
    time.sleep(0.5)
    pain_out = run_pain_point_agent(jtbd_out, persona_out, context=contexts["pain_points"])
    results["AGENT 3 — PAIN POINT ANALYSIS"] = pain_out
    print_section("AGENT 3 — PAIN POINT ANALYSIS", pain_out)

    # Agent 4
    print("\n[4/5] Running Opportunity Scorer...")
    time.sleep(0.5)
    score_out = run_opportunity_scorer(pain_out, context=contexts["opportunities"])
    results["AGENT 4 — OPPORTUNITY SCORING"] = score_out
    print_section("AGENT 4 — OPPORTUNITY SCORING", score_out)

    # Agent 5
    print("\n[5/5] Running PRD Writer...")
    time.sleep(0.5)
    prd_out = run_prd_writer(
        jtbd_output=jtbd_out,
        persona_output=persona_out,
        pain_point_output=pain_out,
        opportunity_output=score_out,
        context=contexts.get("prd", "")
    )
    results["AGENT 5 — PRD"] = prd_out
    print_section("AGENT 5 — PRD", prd_out)

    if save:
        save_report(user_feedback, results)

    return results


def main():
    print("\n" + "=" * 50)
    print("   AI Product Manager — Full Pipeline")
    print("   Powered by 5 specialized agents")
    print("=" * 50)
    print("\nPaste user feedback below.")
    print("Press Enter twice to run the full pipeline.\n")

    while True:
        lines = []
        while True:
            line = input()
            if line == "":
                if lines:
                    break
            else:
                lines.append(line)

        user_feedback = "\n".join(lines).strip()

        if not user_feedback:
            print("Nothing entered. Try again.\n")
            continue

        print("\nStarting pipeline...\n")
        run_pipeline(user_feedback)

        print("\n" + "=" * 50)
        again = input("Run again with new feedback? (yes / no): ").strip().lower()
        if again != "yes":
            print("\nGoodbye!")
            break
        print()


if __name__ == "__main__":
    main()