
from .api import call_model_chat_completions
from concurrent.futures import ThreadPoolExecutor


def getAnswer(text: str, *, allow_llm_retry: bool = True):
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.lower().startswith(("final", "answer", "result")):
            if ":" in ln:
                ans = ln.split(":", 1)[1].strip()
            else:
                parts = ln.split(None, 1)
                ans = parts[1].strip() if len(parts) > 1 else ""
            ans = ans.strip('$').strip()
            if ans:
                return ans
    cleaned = text.strip().strip('$').strip()
    if len(cleaned) < 100 and '\n' not in cleaned:
        return cleaned
    if allow_llm_retry:
        system = "Extract the final answer from the assistant reply. Respond with 'Final: <answer>' only."
        prompt = f"Assistant reply:\n{text}\n\nGive only the final answer."
        r = call_model_chat_completions(prompt, system, temperature=0.0)
        if r.get("ok"):
            return getAnswer(str(r.get("text") or ""), allow_llm_retry=False)
    return None


class Agent:

    def solve(self, problem: str):
        # sc + cot in parallel
        sc_prompt = f"Problem:\n{problem}\n\nGive only the final answer. Do not show any reasoning. End with:\nFinal: <answer>"
        sc_system = "You are a helpful assistant. Always end with 'Final: <answer>' containing only the plain answer (no LaTeX, no $ signs)."
        cot_prompt = f"Problem:\n{problem}\n\nThink briefly (3–4 sentences). Then end with:\nFinal: <answer>"
        cot_system = "You are a helpful assistant. Always end with 'Final: <answer>' containing only the plain answer (no LaTeX, no $ signs)."

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_sc = executor.submit(call_model_chat_completions, sc_prompt, sc_system, temperature=0.7)
            future_cot = executor.submit(call_model_chat_completions, cot_prompt, cot_system, temperature=0.0)
            r_sc = future_sc.result()
            r_cot = future_cot.result()

        sc_ans = getAnswer(str(r_sc.get("text") or "")) if r_sc.get("ok") else None
        print(f"[SC] ans={sc_ans}")
        cot_ans = getAnswer(str(r_cot.get("text") or "")) if r_cot.get("ok") else None
        print(f"[CoT] ans={cot_ans}")

        # candidates for critic
        candidates = []
        if sc_ans:
            candidates.append(sc_ans)
        if cot_ans and cot_ans != sc_ans:
            candidates.append(cot_ans)

        # fallback
        if not candidates:
            system = "Reply with exactly: 'Final: <answer>'"
            follow = f"Problem:\n{problem}\n\nProvide only the final answer."
            r2 = call_model_chat_completions(follow, system, temperature=0.0)
            final = getAnswer(str(r2.get("text") or "")) if r2.get("ok") else None
            print(f"[Fallback] ans={final}")
            return final.strip() if final else ""

        if len(candidates) == 1:
            return candidates[0].strip()

        # disputed then ask critic
        return self.critic(problem, candidates)
    
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
        for test in tests:
            got = self.solve(test["prompt"])
            is_correct = self.grade(test["expected"], got, test.get("type", "exact"))
            rows.append({
                "id": test["id"],
                "expected": test["expected"],
                "got": got,
                "correct": is_correct,
            })

        correct = sum(1 for x in rows if x["correct"])
 #       print(f"accuracy={correct/len(rows):.4f}" if rows else "accuracy=0.0000")
        return rows

    def grade(self, expected: str, got: str, kind: str) -> bool:
        if not expected or not got:
            return False
        query = f"""
        Does the following answer match the expected answer? It does not need to be an exact match.
        If they are equivalent, reply with "YES", otherwise reply with "NO". No reasoning. just one word.
        Expected answer: {expected}
        Given answer: {got}
        """
        return call_model_chat_completions(query, temperature=0.0).get("text", "").strip().upper() == "YES"



# def write_answers_csv(input_path, csv_path):

#     import json
#     import csv
#     from pathlib import Path

#     p = Path(input_path)
#     if not p.exists():
#         raise FileNotFoundError("Input file not found")

#     with p.open("r", encoding="utf-8") as file:
#         data = json.load(file)
#     if not isinstance(data, list):
#         raise ValueError("Input must be a list of question objects")

#     agent = Agent()
#     answers = []
#     for q in data:
#         inp = q.get("input", "")
#         try:
#             out = agent.solve(inp)
#         except Exception:
#             out = ""
#         answers.append(out or "")

#     outp = Path(csv_path)
#     outp.parent.mkdir(parents=True, exist_ok=True)
#     with outp.open("w", encoding="utf-8", newline="") as file:
#         writer = csv.writer(file)
#         writer.writerow(["index", "output"])
#         for i, ans in enumerate(answers, start=1):
#             writer.writerow([i, ans])

#     return str(outp)