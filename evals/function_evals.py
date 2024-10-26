import json
import os
from configs.agents import coordinator_agent
from evals.eval_utils import run_function_evals

import os

current_directory = os.getcwd()

coordinator_test_cases = f"{current_directory}/evals/eval_cases/coordinator_cases.json"


n = 5

if __name__ == "__main__":
    # Run coordinator_agent evals
    with open(coordinator_test_cases, "r") as file:
        coordinator_test_cases = json.load(file)
    run_function_evals(
        coordinator_agent,
        coordinator_test_cases,
        n,
        eval_path=f"{current_directory}/evals/eval_results/coordinator_evals.json",
    )
