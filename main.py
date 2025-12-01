import argparse 	
import json			
from pathlib import Path
from typing import Any, Dict

from src.agent import Agent	


def run(input_path: Path, output_path: Path, limit: int | None, max_calls: int, sc_samples: int):
	"""
	Run the agent
	"""
	# data = data[:]
	if not isinstance(data, list):				
		raise ValueError("Input JSON must be a list of {input, ...} objects")

	if limit is not None:			
		data = data[:limit]

	agent = Agent(max_calls=max_calls, sc_samples=sc_samples) # create agent for solving 

	outputs: list[Dict[str, Any]] = []

	# Process each example
	for ex in data:
		problem = ex.get("input", "")
		gold = ex.get("output")
		pred, meta = agent.solve(problem) #TODO
		outputs.append({
			"input": problem,
			"prediction": pred,
			"gold": gold,
			"calls_used": meta.get("calls_used"),
			"trace": meta,
		})

	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(json.dumps(outputs, indent=2))

# parse arguments
def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", type=str, default="contents/cse476_final_project_dev_data.json")
	parser.add_argument("--output", type=str, default="outputs/output.json")
	parser.add_argument("--limit", type=int, default=None)
	parser.add_argument("--max-calls", type=int, default=12)
	parser.add_argument("--sc-samples", type=int, default=5)
	args = parser.parse_args()

	run(Path(args.input), Path(args.output), args.limit, args.max_calls, args.sc_samples)


if __name__ == "__main__":
	main()
