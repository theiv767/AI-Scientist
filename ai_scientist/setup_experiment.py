import json
import os
import os.path as osp
import time
from typing import List, Dict, Union

import requests

from ai_scientist.llm import get_response_from_llm, extract_json_between_markers, create_client, AVAILABLE_LLMS

S2_API_KEY = os.getenv("S2_API_KEY")

idea_first_prompt = """{task_description}
<experiment.py>
{code}
</experiment.py>


Come up with the next impactful and creative idea for research experiments and directions you can feasibly investigate with the code provided.
Note that you will not have access to any additional resources or datasets.
Make sure any idea is not overfit the specific training dataset or model, and has wider significance.

Respond in the following format:

THOUGHT:
<THOUGHT>

NEW IDEA JSON:
```json
<JSON>
```

In <THOUGHT>, first briefly discuss your intuitions and motivations for the idea. Detail your high-level plan, necessary design choices and ideal outcomes of the experiments. Justify how the idea is different from the existing ones.

In <JSON>, provide the new idea in JSON format with the following fields:
- "Name": A shortened descriptor of the idea. Lowercase, no spaces, underscores allowed.
- "Title": A title for the idea, will be used for the report writing.
- "Experiment": An outline of the implementation. E.g. which functions need to be added or modified, how results will be obtained, ...
- "Interestingness": A rating from 1 to 10 (lowest to highest).
- "Feasibility": A rating from 1 to 10 (lowest to highest).
- "Novelty": A rating from 1 to 10 (lowest to highest).

Be cautious and realistic on your ratings.
This JSON will be automatically parsed, so ensure the format is precise.
You will have {num_reflections} rounds to iterate on the idea, but do not need to use them all.
"""

idea_reflection_prompt = """Round {current_round}/{num_reflections}.
In your thoughts, first carefully consider the quality, novelty, and feasibility of the idea you just created.
Include any other factors that you think are important in evaluating the idea.
Ensure the idea is clear and concise, and the JSON is the correct format.
Do not make things overly complicated.
In the next attempt, try and refine and improve your idea.
Stick to the spirit of the original idea unless there are glaring issues.

Respond in the same format as before:
THOUGHT:
<THOUGHT>

NEW IDEA JSON:
```json
<JSON>
```

If there is nothing to improve, simply repeat the previous JSON EXACTLY after the thought and include "I am done" at the end of the thoughts but before the JSON.
ONLY INCLUDE "I am done" IF YOU ARE MAKING NO MORE CHANGES."""



# GENERATE IDEAS
def generate_experiment(
    base_dir,
    client,
    model,
    num_reflections=5
):

    # get prompts
    with open(osp.join(base_dir, "prompt.json"), "r") as f:
        prompt = json.load(f)

    idea_system_prompt = prompt["system"]
    task_description=prompt["task_description"]


    # get code
    with open(osp.join(base_dir, "experiment.py"), "r") as f:
        code = f.read()


    #lista de experimentos falhos
    experiment_failures = []

    msg_history = []

    text, msg_history = get_response_from_llm(
                idea_first_prompt.format(
                    task_description=prompt["task_description"],
                    code=code,
                    num_reflections=num_reflections,
                ),
                client=client,
                model=model,
                system_message=idea_system_prompt,
                msg_history=msg_history,
            )
    

def generate_plot(
    base_dir,
    client,
    model,
    num_reflections
):
    with open(osp.join(base_dir, "prompt.json"), "r") as f:
        prompt = json.load(f)    

    idea_system_prompt = prompt["system"]    
    task_description=prompt["task_description"]

    #final_info
    with open(osp.join(base_dir, "run_0", "final_info.json"), "r") as f:
        baseline_results = json.load(f)

    pass




def experiment_exists(base_dir) -> bool:
    # Verifica se o arquivo 'experiment.py' existe no diretório base
    experiment_path = osp.join(base_dir, "experiment.py")
    
    if not osp.exists(experiment_path):
        return False
    
    with open(experiment_path, "r") as f:
        code = f.read()
    

    if "final_info" in code and "means" in code:
        return True
    
    return False





if __name__ == "__main__":
    NUM_REFLECTIONS = 5
    import argparse

    parser = argparse.ArgumentParser(description="Generate AI scientist ideas")
    args = parser.parse_args()


    client, client_model = create_client(args.model)
    base_dir = osp.join("templates", args.experiment)
    results_dir = osp.join("results", args.experiment)



    if not experiment_exists(base_dir=base_dir):
        code = generate_experiment(
            base_dir,
            client=client,
            model=client_model,
            num_reflections=NUM_REFLECTIONS
        )   

        plot = generate_plot(
            base_dir,
            client=client,
            model=client_model,
            num_reflections=NUM_REFLECTIONS
        )

