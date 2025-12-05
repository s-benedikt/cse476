import re
from .api import call_model_chat_completions


def getAnswer(text: str):
    # Prefer explicit 'Final:' tail
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.lower().startswith("final:"):
            return ln.split(":", 1)[1].strip()

    # try last number
    m_all = re.findall(r"-?\d+\.\d+|-?\d+/\d+|-?\d+", text)
    if m_all:
        return m_all[-1] 
    else:
        # return last word
        words = re.findall(r"\S+", text)
        if words:
            return words[-1]
        else:   
            return None # nothing found (worst case)


class Agent:

    def solve(self, problem: str):
        plan = call_model_chat_completions(
            f"Problem:\n{problem}\n\nGive 2 short bullet steps.",
            "Be concise.", temperature=0.0, timeout=10
        ).get("text") or ""

        prompt = f"Problem:\n{problem}\n\nPlan:\n{plan}\n\nSolve. End with 'Final: <answer>'."
        votes = {}
        for t in (0.0, 0.4, 0.8):
            r = call_model_chat_completions(prompt, "Solve carefully.", temperature=t, timeout=10)
            ans = getAnswer(str(r.get("text") or "")) if r.get("ok") else None
            if ans:
                votes[ans] = votes.get(ans, 0) + 1

        if not votes:
            return ""
        candidate = max(votes.items(), key=lambda x: x[1])[0]

        checked = self.critic(problem, candidate)
        return (checked.get("final") or candidate or "").strip()

    def critic(self, problem: str, answer: str):
        system = "You are a strict critic. Output only the final answer."
        prompt = (
            f"Problem:\n{problem}\n\nProposed answer: {answer}\n"
            "Verify. If wrong, provide the corrected final answer."
        )
        r = call_model_chat_completions(prompt, system, temperature=0.0, timeout=10)
        final = getAnswer(str(r.get("text") or "")) if r.get("ok") else None
        return {"ok": r.get("ok"), "text": r.get("text"), "final": final}


def batch_solve_questions(questions: list) -> list:
    agent = Agent()
    outputs = []
    for q in questions:
        input = q.get("input", "")
        try:
            out = agent.solve(input)
        except Exception:
            out = ""
        if out is None:
            out = ""
        outputs.append(str(out).strip())
    return outputs

def write_answers_csv(input_path, csv_path):
    import json
    import csv
    from pathlib import Path

    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found")

    with p.open("r") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("Input must be a list of question objects")

    answers = batch_solve_questions(data)

    outp = Path(csv_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["index", "output"])
        for i, ans in enumerate(answers, start=1):
            writer.writerow([i, ans])

    return str(outp)