import re
from typing import List, Dict

from .api import call_model_chat_completions


def getAnswer(text: str):           
    # pattern to match all floats, fractions, or integers
    pattern = r"-?\d+\.\d+|-?\d+/\d+|-?\d+" 

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()] 

    # check in reverse for keyword
    for ln in reversed(lines):
        if ln.lower().startswith("final:"):
            # strip junk
            tail = ln.split(":", 1)[1].strip()
            # get number
            m = re.search(pattern, tail)
            return m.group(0) if m else None

    # fallback returns last number
    matches = re.findall(pattern, text)
    if matches:
        answer = matches[-1]
        return answer
    return None

class Agent:

    def solve(self, problem: str):
        calls_used = 0

        plan_prompt = (
            f"Problem:\n{problem}\n\n"
            "Generate a concise 2-3 step plan with bullet points."
        )
        plan_query = "Solve math problems. Keep the plan short."
        plan_response = call_model_chat_completions(plan_prompt, plan_query, temperature=0.2, timeout=10)
        calls_used += 1

        plan_text = plan_response.get("text") or ""
        final_prompt = (
            f"Problem:\n{problem}\n\nPlan:\n{plan_text}\n\n"
            "Solve step by step. Show final answer as 'Final: <answer>'."
        )
        solve_response = call_model_chat_completions(final_prompt, "Solve math problems step by step.", temperature=0.0, timeout=10)
        calls_used += 1

        candidate0 = getAnswer(str(solve_response.get("text") or "")) if solve_response.get("ok") else None
        if candidate0 is not None:
            checked = self.critic(problem, candidate0)

            final = checked.get("final") or candidate0
            return final
        # Self-consistency sampling
 

    def critic(self, problem: str, answer: str):
        system = (
            "You are a critic. Check the following answer. "
            "If incorrect, compute the correct one. Output only the final number."
        )
        prompt = (
            f"Problem:\n{problem}\n\nProposed answer: {answer}\n"
            "Verify. If wrong, provide the corrected final number. Output only the number."
        )
        r = call_model_chat_completions(prompt, system, temperature=0.0, timeout=10)
        final = getAnswer(str(r.get("text") or "")) if r.get("ok") else None
        return {"ok": r.get("ok"), "text": r.get("text"), "final": final}