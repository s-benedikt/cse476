
from .api import call_model_chat_completions


def getAnswer(text: str):

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.lower().startswith(("final", "answer", "result")):
            ans = ln.split(":", 1)[1].strip()
            # remove latex
            ans = ans.strip('$').strip()
            return ans
    cleaned = text.strip().strip('$').strip()
    if len(cleaned) < 100 and not '\n' in cleaned:
        return cleaned
    return None


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
    
    def critic(self, problem: str, candidates: list) -> str:
        """Ask critic to select the best answer from multiple candidates."""
        cands_str = "\n".join([f"Option {i+1}: {c}" for i, c in enumerate(candidates)])
        system = "You are a strict critic. Evaluate the options and output JUST THE VALUE of the correct answer, not the option label. Do not provide any explanation."
        prompt = (
            f"Problem:\n{problem}\n\n{cands_str}\n\n"
            "Which option is correct? Reply with the actual answer value in the format: Final: <answer value>\n"
            "Do NOT reply with 'Option 1' or 'Option 2' - reply with the actual numeric/text answer. Do not provide any explanation."
        )
        r = call_model_chat_completions(prompt, system, temperature=0.0)
        final = getAnswer(str(r.get("text") or "")) if r.get("ok") else None
        print(f"[Critic] selected={final}")
        if not final or final.lower().startswith('option'):
            return candidates[0].strip()
        return final.strip()

    def evaluate_tests(self, tests):
        rows = []
        for t in tests:
            got = self.solve(t["prompt"])
            is_correct = self.grade(t["expected"], got, t.get("type", "exact"))
            rows.append({
                "id": t["id"],
                "expected": t["expected"],
                "got": got,
                "correct": is_correct,
            })

        correct = sum(1 for x in rows if x["correct"])
        print(f"accuracy={correct/len(rows) if rows else 0}")
        return rows

    def grade(self, expected: str, got: str, kind: str) -> bool:
        if not expected or not got:
            return False
        return str(expected).strip().lower() == str(got).strip().lower()



def write_answers_csv(input_path, csv_path):

    import json
    import csv
    from pathlib import Path

    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError("Input file not found")

    with p.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("Input must be a list of question objects")

    agent = Agent()
    answers = []
    for q in data:
        inp = q.get("input", "")
        try:
            out = agent.solve(inp)
        except Exception:
            out = ""
        answers.append(out or "")

    outp = Path(csv_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["index", "output"])
        for i, ans in enumerate(answers, start=1):
            writer.writerow([i, ans])

    return str(outp)