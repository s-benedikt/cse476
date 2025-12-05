import argparse 	
import json			
from pathlib import Path
from typing import Any, Dict

from src.agent import Agent	


def run(input_path: Path, output_path: Path):
	"""
	Run the agent
	"""
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

	# Process each example
	for ex in data:
		problem = ex.get("input", "")
		gold = ex.get("output")
		pred = agent.solve(problem)
		outputs.append({
			"input": problem,
			"prediction": pred,
			"gold": gold,
		})

	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(json.dumps(outputs, indent=2), encoding="utf-8")

# parse arguments
def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", type=str, default="contents/cse476_final_project_dev_data.json")
	parser.add_argument("--output", type=str, default="outputs/output.json")
	args = parser.parse_args()

	run(Path(args.input), Path(args.output))

if __name__ == "__main__":
	main()
