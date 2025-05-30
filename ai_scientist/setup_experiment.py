import json
import os
import sys
import os.path as osp
import time
from typing import List, Dict, Union

from aider.coders import Coder
from aider.io import InputOutput
from aider.models import Model
from datetime import datetime

import requests

from ai_scientist.generate_experiment import generate_experiment
from ai_scientist.generate_experiment import generate_experiment_plot
from ai_scientist.llm import get_response_from_llm, extract_json_between_markers, create_client, AVAILABLE_LLMS

S2_API_KEY = os.getenv("S2_API_KEY")



metric_first_prompt = """{task_description}

Here are the metrics you have already generated:

'''
{prev_metrics_string}
'''

Your task is to propose a new scientific metric that is:

- Quantifiable and clearly defined
- Useful for evaluating the success or failure of the scientific objective stated above
- Able to support or refute hypotheses based on empirical results
- Suitable for monitoring changes or trends
- Expressed in a form that ensures reproducibility and objectivity
- Not overfitted to any specific dataset or model, and instead based on generalizable principles

Describe the metric in a concise way, including its name, what it measures, how it is calculated, and why it is useful in the context of the objective. Do not invent data or assume access to external sources.

Note that you will not have access to any additional resources or datasets.
Make sure that no metric is overfitted to the specific dataset or training model and has a broader meaning.

Respond in the following format:

THOUGHT:
<THOUGHT>

NEW JSON IDEA:
```json
<JSON>
```

In <THOUGHT>, first briefly discuss your intuitions and motivations for the metric. Detail your high-level plan, the design choices needed, and how the new metric will help measure the results you achieve. Justify how the metric is different from the existing ones.

In <JSON>, provide the new idea in JSON format with the following fields:
- "Name": A shortened descriptor of the metric. Lowercase, no spaces, underscores allowed.
- "Title": A title for the metric, will be used for the report writing.
- "Definition": A clear and precise description of what the metric measures. It should make it clear what is being quantified.
- "Limitations": Point out weaknesses in the metric, such as contexts in which it may generate misleading interpretations or failure to reflect actual performance.
- "Dependencies": Clearly list what data, variables, or intermediate results are needed to calculate the metric.

Be cautious and realistic about your ratings.
This JSON will be automatically parsed, so ensure the format is precise.
You will have {num_reflections} rounds to iterate on the idea, but do not need to use them all.
"""


metric_reflection_prompt = """Round {current_round}/{num_reflections}.
In your thoughts, first carefully consider the clarity, relevance, and usefulness of the metric you just created for evaluating the implementation of the idea.
Include any other factors that you think are important in assessing the quality of this metric, such as objectivity, measurability, and alignment with the goals of the original idea.
Ensure the metric is clear and concise, and the JSON is in the correct format.
Do not make things overly complicated.
In the next attempt, try to refine and improve your metric.
Stick to the spirit of the original metric unless there are glaring issues.

Respond in the same format as before:

THOUGHT:
<THOUGHT>

NEW METRIC JSON:
```json
<JSON>

If there is nothing to improve, simply repeat the previous JSON EXACTLY after the thought and include "I am done" at the end of the thoughts but before the JSON.
ONLY INCLUDE "I am done" IF YOU ARE MAKING NO MORE CHANGES."""




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



def search_similar_metrics(task_description: str, num_results: int = 5) -> List[str]:
    # use Semantic Scholar API here
    # extract titles + snippets related to evaluation metrics
    # return list of candidate metric names or descriptions
    pass


def generate_metrics(
        base_dir,
        client,
        model,
        skip_generation=False,
        max_num_generations=5,
        num_reflections=5,
):
    if skip_generation:
        try:
            with open(osp.join(base_dir, "metrics.json"), "r") as f:
                metrics = json.load(f)
            print("Loaded existing metrics:")
            for metric in metrics:
                print(metric)
            return metrics
        except FileNotFoundError:
            print("No existing metrics found. Generating new metrics.")
        except json.JSONDecodeError:
            print("Error decoding existing metrics. Generating new metrics.")

    metric_str_archive = []
    seed_file = osp.join(base_dir, "seed_metrics.json")
    if osp.exists(seed_file):
        with open(seed_file, "r") as f:
            seed_metrics = json.load(f)
        for seed_metric in seed_metrics:
            metric_str_archive.append(json.dumps(seed_metric))


    with open(osp.join(base_dir, "prompt.json"), "r") as f:
        prompt = json.load(f)

    idea_system_prompt = prompt["system"]
    task_description = prompt["task_description"]


    # TO DO ---------------------------------------------------------------------
    # MELHORAR O PROMPT 'metric_first_prompt' COM RESULTADOS DO semantic_schoolar
    # OBS:
    # - criar qry para semantic_schoolar buscando métricas comuns para o problema descrito em system e task_description
    # - concatenar resultados relevantes no 'metric_first_prompt'
    #----------------------------------------------------------------------------

    for i in range(max_num_generations):
        print()
        print(f"Generating metric {i + 1}/{max_num_generations}")
        try:
            prev_metrics_string = "\n\n".join(metric_str_archive)

            msg_history = []
            print(f"Iteration 1/{num_reflections}")
            text, msg_history = get_response_from_llm(
                metric_first_prompt.format(
                    task_description=task_description,
                    prev_metrics_string=prev_metrics_string,
                    num_reflections=num_reflections,
                ),
                client=client,
                model=model,
                system_message=idea_system_prompt,
                msg_history=msg_history,
            )

            json_output = extract_json_between_markers(text)
            assert json_output is not None, "Failed to extract JSON from LLM output"
            print(json_output)

            if num_reflections > 1:
                for j in range(num_reflections - 1):

                    # TO DO ---------------------------------------------------------------------
                    # MELHORAR O PROMPT 'metric_reflection_prompt' COM RESULTADOS DO semantic_schoolar
                    # OBS:
                    # - criar qry para semantic_schoolar com base em dados da métrica e sua usabilidade no meio academico, comparando com o problema atual
                    # - concatenar resultados relevantes no 'metric_reflection_prompt'
                    #----------------------------------------------------------------------------

                    print(f"Iteration {j + 2}/{num_reflections}")
                    text, msg_history = get_response_from_llm(
                        metric_reflection_prompt.format(
                            current_round=j + 2, num_reflections=num_reflections
                        ),
                        client=client,
                        model=model,
                        system_message=idea_system_prompt,
                        msg_history=msg_history,
                    )

                    json_output = extract_json_between_markers(text)
                    assert json_output is not None, "Failed to extract JSON from LLM output"
                    print(json_output)

                    if "I am done" in text:
                        print(f"Metric generation converged after {j + 2} iterations.")
                        break

            metric_str_archive.append(json.dumps(json_output))
        except Exception as e:
            print(f"Failed to generate metric: {e}")
            continue

    metrics = [json.loads(m) for m in metric_str_archive]
    with open(osp.join(base_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=4)

    return metrics



def generate_next_metric(
        base_dir,
        client,
        model,
        prev_metric_archive=[],
        num_reflections=5,
        max_attempts=10,
):
    metric_archive = prev_metric_archive
    original_archive_size = len(metric_archive)

    print(f"Generating metric {original_archive_size + 1}")

    if len(prev_metric_archive) == 0:
        print("First iteration, taking seed metrics")
        with open(osp.join(base_dir, "seed_metrics.json"), "r") as f:
            seed_metrics = json.load(f)
        for seed_metric in seed_metrics[:1]:
            metric_archive.append(seed_metric)
    else:
        with open(osp.join(base_dir, "prompt.json"), "r") as f:
            prompt = json.load(f)

        idea_system_prompt = prompt["system"]
        task_description = prompt["task_description"]

        for _ in range(max_attempts):
            try:
                prev_metrics_string = "\n\n".join(
                    [json.dumps(metric) for metric in metric_archive]
                )

                msg_history = []
                print(f"Iteration 1/{num_reflections}")
                text, msg_history = get_response_from_llm(
                    metric_first_prompt.format(
                        task_description=task_description,
                        prev_metrics_string=prev_metrics_string,
                        num_reflections=num_reflections
                    ),
                    client=client,
                    model=model,
                    system_message=idea_system_prompt,
                    msg_history=msg_history,
                )

                json_output = extract_json_between_markers(text)
                assert json_output is not None, "Failed to extract JSON from LLM output"
                print(json_output)

                if num_reflections > 1:
                    for j in range(num_reflections - 1):
                        print(f"Iteration {j + 2}/{num_reflections}")
                        text, msg_history = get_response_from_llm(
                            metric_reflection_prompt.format(
                                current_round=j + 2,
                                num_reflections=num_reflections,
                            ),
                            client=client,
                            model=model,
                            system_message=idea_system_prompt,
                            msg_history=msg_history,
                        )

                        json_output = extract_json_between_markers(text)
                        assert json_output is not None, "Failed to extract JSON from LLM output"
                        print(json_output)

                        if "I am done" in text:
                            print(f"Metric generation converged after {j + 2} iterations.")
                            break

                metric_archive.append(json_output)
                break
            except Exception as e:
                print(f"Failed to generate metric: {e}")
                continue

    with open(osp.join(base_dir, "metrics.json"), "w") as f:
        json.dump(metric_archive, f, indent=4)

    return metric_archive




def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def generate_code(
    base_dir,
    client,
    model,
    metrics,
    num_reflections=5,
    log_file=False,
):
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results_folder_name = osp.join(base_dir, "setup")
    os.makedirs(results_folder_name, exist_ok=True)


    exp_file = osp.join(base_dir, "experiment.py")
    #vis_file = osp.join(base_dir, "plot.py")
    notes = osp.join(results_folder_name, "notes.txt")
    with open(notes, "w") as f:
        f.write(f"# Title: base_code\n")
        f.write(f"Results: {results_folder_name}\n")
        f.write(f"Description: Baseline results.\n")
    if log_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        log_path = osp.join(results_folder_name, "log.txt")
        log = open(log_path, "a")
        sys.stdout = log
        sys.stderr = log



    fnames = [exp_file, notes]

    chat_history_file = os.path.join(results_folder_name, "code_aider.txt")
    io = InputOutput(
        yes=True, chat_history_file=chat_history_file
    )

    if model == "deepseek-coder-v2-0724":
        main_model = Model("deepseek/deepseek-coder")
    elif model == "deepseek-reasoner":
        main_model = Model("deepseek/deepseek-reasoner")
    elif model == "deepseek-chat":
        main_model = Model("deepseek/deepseek-chat")
    elif model == "llama3.1-405b":
        main_model = Model("openrouter/meta-llama/llama-3.1-405b-instruct")
    else:
        main_model = Model(model)

    coder = Coder.create(
        main_model=main_model,
        fnames=fnames,
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )

    print_time()
    print(f"*Generating Experiment*")
    try:
        success = generate_experiment(base_dir, metrics, coder, results_folder_name)

    except Exception as e:
        print(f"Error during experiment generation: {e}")
        print(f"Experiment failed")
        return False

    if not success:
        print(f"Experiment failed")
        return False


    print_time()
    print(f"*Finish Experiment Generation*")



def generate_plot(
    base_dir,
    client,
    model,
    num_reflections=5,
    log_file=False,
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results_folder_name = osp.join(base_dir, "setup")
    os.makedirs(results_folder_name, exist_ok=True)


    exp_file = osp.join(base_dir, "plot.py")
    #vis_file = osp.join(base_dir, "plot.py")
    notes = osp.join(results_folder_name, "notes.txt")
    with open(notes, "w") as f:
        f.write(f"# Title: base_code\n")
        f.write(f"Results: {results_folder_name}\n")
        f.write(f"Description: Baseline results.\n")
    if log_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        log_path = osp.join(results_folder_name, "log.txt")
        log = open(log_path, "a")
        sys.stdout = log
        sys.stderr = log



    fnames = [exp_file, notes]

    chat_history_file = os.path.join(results_folder_name, "code_aider.txt")
    io = InputOutput(
        yes=True, chat_history_file=chat_history_file
    )

    if model == "deepseek-coder-v2-0724":
        main_model = Model("deepseek/deepseek-coder")
    elif model == "deepseek-reasoner":
        main_model = Model("deepseek/deepseek-reasoner")
    elif model == "deepseek-chat":
        main_model = Model("deepseek/deepseek-chat")
    elif model == "llama3.1-405b":
        main_model = Model("openrouter/meta-llama/llama-3.1-405b-instruct")
    else:
        main_model = Model(model)

    coder = Coder.create(
        main_model=main_model,
        fnames=fnames,
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )

    print_time()
    print(f"*Generating Plot*")
    try:
        success = generate_experiment_plot(base_dir, coder, results_folder_name)

    except Exception as e:
        print(f"Error during plot generation: {e}")
        print(f"Plot failed")
        return False

    if not success:
        print(f"Plot failed")
        return False


    print_time()
    print(f"*Finish Plot Generation*")





def setup_experiment(
    base_dir,
    client,
    model,
    num_reflections

):
    NUM_REFLECTIONS = 5
    import argparse

    parser = argparse.ArgumentParser(description="Generate AI scientist initial experiment, metrics e plots")
    # add type of experiment (nanoGPT, Boston, etc.)
    parser.add_argument(
        "--experiment",
        type=str,
        default="julIA",
        help="Experiment to run AI Scientist on.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-chat",
        choices=AVAILABLE_LLMS,
        help="Model to use for AI Scientist.",
    )
    parser.add_argument(
        "--skip-idea-generation",
        action="store_true",
        help="Skip idea generation and use existing ideas.",
    )
    parser.add_argument(
        "--check-novelty",
        action="store_true",
        help="Check novelty of ideas.",
    )

    parser.add_argument(
        "--skip-metric-generation",
        action="store_true",
        help="Skip idea generation and use existing ideas.",
    )

    args = parser.parse_args()


    client, client_model = create_client(args.model)
    base_dir = osp.join("templates", args.experiment)
    results_dir = osp.join("results", args.experiment)



    if not experiment_exists(base_dir=base_dir):
        metrics = generate_metrics(
            base_dir=base_dir,
            client=client,
            model=model,
            skip_generation=True
        )

        code = generate_code(
            base_dir,
            client=client,
            model=client_model,
            metrics=metrics,
            num_reflections=NUM_REFLECTIONS
        )   

        plot = generate_plot(
            base_dir,
            client=client,
            model=client_model,
            num_reflections=NUM_REFLECTIONS
        )

