import json
import os
import os.path as osp
import shutil
import subprocess
import sys
from subprocess import TimeoutExpired

import hashlib



MAX_ATTEMPTS = 5
MAX_REFLECTIONS = 3
MAX_STDERR_OUTPUT = 1500


coder_experiment_prompt = """Your goal is to create a minimal but functional experiment from scratch, based on the following task description:

## Task:
{task_description}

## Objective:
Implement a simple and self-contained experiment in Python. This experiment should reflect the task above and report relevant results.

You must create a single file named `experiment.py`. This script must:
- Be executable with the command `python experiment.py --out_dir=run_0`
- Save the experiment results in a file called `final_info.json` inside the folder `run_0` (create it if it doesn't exist)
- The `final_info.json` file must contain a JSON object with the following structure:

  {{
    "{result_title}": {{
      "means": {{
        "metric1": value,
        "metric2": value,
        "...": "..."
      }}
    }}
  }}

Example of `final_info.json` contents:

{{
  "shakespeare_char": {{
    "means": {{
      "final_train_loss_mean": 0.8186,
      "best_val_loss_mean": 1.4654,
      "total_train_time_mean": 77.2694,
      "avg_inference_tokens_per_second_mean": 666.5076
    }}
  }}
}}

- Include all code necessary to run the experiment from scratch (use mock data or basic examples as needed)
- Report at least the following metrics: {metrics}
- Be as clear and modular as possible, but not overly complex

## Constraints:
- Do not include extra explanations, only the necessary code.

After you complete each change, we will run the command `python experiment.py --out_dir=run_0`.
YOUR PROPOSED CHANGE MUST USE THIS COMMAND FORMAT, DO NOT ADD ADDITIONAL COMMAND LINE ARGS.
You can then implement the next thing on your list.
"""


def hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()

def run_experiment(folder_name, timeout=600):
    cwd = os.path.abspath(folder_name)
    command = ["python", "experiment.py", "--out_dir=run_0"]
    try:
        result = subprocess.run(command, cwd=cwd, stderr=subprocess.PIPE, text=True, timeout=timeout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"Experiment failed with return code {result.returncode}")
            stderr_output = result.stderr
            if len(stderr_output) > MAX_STDERR_OUTPUT:
                stderr_output = "..." + stderr_output[-MAX_STDERR_OUTPUT:]
            return False, stderr_output

        final_info_path = os.path.join(cwd, "run_0", "final_info.json")
        if not os.path.exists(final_info_path):
            return False, "Missing final_info.json"

        try:
            with open(final_info_path, "r") as f:
                data = json.load(f)

            if not isinstance(data, dict) or not data:
                return False, "final_info.json is not a non-empty dictionary"

            for dataset, info in data.items():
                if not isinstance(info, dict) or "means" not in info:
                    return False, f"Missing 'means' key in dataset '{dataset}'"

        except json.JSONDecodeError:
            return False, "final_info.json is not a valid JSON file"


        return True, ""
    except TimeoutExpired:
        return False, "Timeout"

def generate_experiment(base_dir, metrics, coder, feedback_folder_name):
    with open(osp.join(base_dir, "prompt.json"), "r") as f:
        prompt = json.load(f) 

    idea_system_prompt = prompt["system"]
    task_description=prompt["task_description"]

    result_title = "autogen_result"
    prompt_base = coder_experiment_prompt.format(
        task_description=task_description, 
        metrics=metrics, 
        result_title=result_title                              
    )


    attempts = 0
    failed_codes = set()

    while attempts < MAX_ATTEMPTS:
        next_prompt = prompt_base
        
        coder_out = coder.run(next_prompt)

        success, feedback = run_experiment(base_dir)


        # TO DO ---------------------------------------------------------------------
        # PEDIR PARA UMA LLM REVISAR O CÓDIGO: 
        # OBS:
        # - para entender se o código realmente faz sentido para o problema e porque. (isso é para evitar código que rodam, mas são inúteis)
        # - salvar a resposta em notes.txt
        # - caso a resposta seja negativa, então o sucess fica false
        #----------------------------------------------------------------------------
        if success:
            return True

        for _ in range(MAX_REFLECTIONS):
            coder_out = coder.run("""The last attempt failed with the following error:

{feedback}

Please revise the `experiment.py` code accordingly. Do not explain, your task is to analyze and modify the contents of the `experiment.py` file in order to fix the error.
""".format(feedback=feedback))
            

            success, feedback = run_experiment(base_dir)
            if success:
                return True


        #failed_codes.add()
        #attempts += 1

    print("Failed to generate a working experiment after all attempts.")
    return False








coder_plot_prompt = """Your task is to create a Python script called `plot.py` that generates appropriate visualizations for experiment results stored in a JSON file `final_info.json`.

## Objectives:
- Load the data from the `final_info.json` file located in the `run_0` directory
- Use standard Python visualization libraries (e.g. matplotlib, seaborn, pandas) to plot visualizations that communicate the results clearly
- Save all generated graphs as image files in the same directory as the input file

## Constraints:
- Do not include explanations or comments in the output
- The script must be executable with the command: `python plot.py`
- All output files (e.g., images) must be saved in the run_0 directory


Below are the contents of the `final_info.json` file that your script should use:

## Contents of `final_info.json`:
{final_info}

After generation, we will run: `python plot.py`
DO NOT require or use any other command-line arguments.
"""

def run_plotting(folder_name, timeout=600):
    cwd = osp.abspath(folder_name)
    # LAUNCH COMMAND
    command = [
        "python",
        "plot.py",
    ]
    try:
        result = subprocess.run(
            command, cwd=cwd, stderr=subprocess.PIPE, text=True, timeout=timeout
        )

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"Plotting failed with return code {result.returncode}")
            stderr_output = result.stderr
            if len(stderr_output) > MAX_STDERR_OUTPUT:
                stderr_output = "..." + stderr_output[-MAX_STDERR_OUTPUT:]
            return False, stderr_output
        
        
        return True, ""
    except TimeoutExpired:
        print(f"Plotting timed out after {timeout} seconds")
        next_prompt = f"Plotting timed out after {timeout} seconds"
        return 1, next_prompt
    

def generate_experiment_plot(base_dir, coder, feedback_folder_name):

    with open(osp.join(base_dir, "run_0", "final_info.json"), "r") as f:
      baseline_results = json.load(f)


    prompt_base = coder_plot_prompt.format(
      final_info=baseline_results
    )


    attempts = 0
    failed_codes = set()

    while attempts < MAX_ATTEMPTS:
        next_prompt = prompt_base
        
        coder_out = coder.run(next_prompt)

        success, feedback = run_plotting(base_dir)


        # TO DO ---------------------------------------------------------------------
        # PEDIR PARA UMA LLM REVISAR O CÓDIGO: 
        # OBS:
        # - para entender se o código realmente faz sentido para o problema e porque. (isso é para evitar código que rodam, mas são inúteis)
        # - salvar a resposta em notes.txt
        # - caso a resposta seja negativa, então o sucess fica false
        #----------------------------------------------------------------------------
        if success:
            return True

        for _ in range(MAX_REFLECTIONS):
            coder_out = coder.run("""The last attempt failed with the following error:

{feedback}

Please revise the `plot.py` code accordingly. Do not explain, your task is to analyze and modify the contents of the `plot.py` file in order to fix the error.
""".format(feedback=feedback))

            success, feedback = run_plotting(base_dir)
            if success:
                return True


        failed_codes.add()
        attempts += 1

    print("Failed to generate a working plot after all attempts.")
    return False