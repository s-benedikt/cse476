import argparse 	
import json		
from pathlib import Path
from typing import Any, Dict

import subprocess
from pathlib import Path as Path
from src.agent import Agent
from concurrent.futures import ThreadPoolExecutor


def run(input_path: Path, output_path: Path):
	if not input_path.exists():
		raise FileNotFoundError(f"Input file not found: {input_path}")
	data_text = input_path.read_text(encoding="utf-8")
	try:
		data = json.loads(data_text)
	except json.JSONDecodeError as e:
		raise ValueError(f"Input file is not valid JSON: {e}") from e

	if not isinstance(data, list):				
		raise ValueError("Input JSON must be a list of {input, ...} objects")



	try:
		agent = Agent() 
	except Exception as e:
		raise RuntimeError(f"Failed to create Agent: {e}") from e
	
	outputs: list[Dict[str, Any]] = []
	output_path.parent.mkdir(parents=True, exist_ok=True)

	def solve_example(item):
		i, example = item
		problem = example.get("input", "")
		gold = example.get("output")
		pred = agent.solve(problem)
		return i, problem, gold, pred

	with ThreadPoolExecutor() as executor:
		solved = list(executor.map(solve_example, enumerate(data, start=1)))

	for i, problem, gold, pred in solved:
		gold_display = gold if gold is not None else "N/A"
		print(f"question {i}: prediction: {pred} gold: {gold_display}")
		outputs.append({
			"input": problem,
			"prediction": pred,
			"gold": gold,
		})


	output_path.write_text(json.dumps(outputs, indent=2), encoding="utf-8")

# parse arguments
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", type=str, default="contents/cse476_final_project_dev_data.json")
	parser.add_argument("--output", type=str, default="outputs/output.json")
	args = parser.parse_args()


	csv_out = Path("outputs/agent_answers.csv")
	run(Path(args.input), Path(args.output))
	return json.loads(Path(args.output).read_text(encoding="utf-8"))

if __name__ == "__main__":
	main()