import json
from collections import defaultdict
from pathlib import Path

DST_PATH = Path(__file__).parent / "COMBINED-RESULTS.json"


def read_json_files():
    data_dir = Path(__file__).parent
    data_dict = {}
    for path in data_dir.iterdir():
        if not path.name.endswith(".json") or path.name == DST_PATH.name:
            continue
        with open(path, "r") as f:
            data = json.load(f)
            model_id = path.name.split("_")[0]
            if "-perf-instruct_" in path.name:
                model_id = model_id + " (⏩)"
            data_dict[model_id] = data
    return data_dict


def model_compete(model1: dict, model2: dict, metric: str):
    model1_wins = 0
    ties = 0
    model2_wins = 0
    for task in model1.keys():
        if model1[task][metric] is None or model2[task][metric] is None:
            continue
        if model1[task][metric] > model2[task][metric]:
            model1_wins += 1
        elif model1[task][metric] < model2[task][metric]:
            model2_wins += 1
        else:
            ties += 1
    return model1_wins, ties, model2_wins


def modelwise_winrate(model_id: str, data: dict, metric: str):
    all_models = list(data.keys())
    other_models = [model for model in all_models if model != model_id]
    all_wins = 0
    all_ties = 0
    all_rounds = len(other_models)
    for other_model in other_models:
        ldps, rdps = compute_aligned_dps_pair(data, model_id, other_model)

        if ldps > rdps:
            all_wins += 1
        elif ldps == rdps:
            all_ties += 1

    all_adj_win = all_wins + all_ties / 2
    return all_adj_win / all_rounds


def taskwise_winrate(model_id: str, data: dict, metric: str):
    all_models = list(data.keys())
    other_models = [model for model in all_models if model != model_id]
    all_wins = 0
    all_ties = 0
    all_rounds = 0
    for other_model in other_models:
        model1_wins, ties, model2_wins = model_compete(
            data[model_id]["eval"], data[other_model]["eval"], metric
        )
        all_wins += model1_wins
        all_ties += ties
        all_rounds += model1_wins + ties + model2_wins

    all_adj_win = all_wins + all_ties / 2
    return all_adj_win / all_rounds


def compute_modelwise_winrates(data: dict, metric: str):
    win_rates = {}
    for model_id in data.keys():
        win_rates[model_id] = modelwise_winrate(model_id, data, metric)
    return win_rates


def compute_taskwise_winrates(data: dict, metric: str):
    win_rates = {}
    for model_id in data.keys():
        win_rates[model_id] = taskwise_winrate(model_id, data, metric)
    return win_rates


def compute_aligned_dps_pair(data: dict, model1: str, model2: str):
    model1_pass_tasks = set(
        task
        for task, result in data[model1]["eval"].items()
        if result["dps"] is not None
    )
    model2_pass_tasks = set(
        task
        for task, result in data[model2]["eval"].items()
        if result["dps"] is not None
    )
    common_tasks = model1_pass_tasks & model2_pass_tasks
    return sum(data[model1]["eval"][t]["dps"] for t in common_tasks) / len(
        common_tasks
    ), sum(data[model2]["eval"][t]["dps"] for t in common_tasks) / len(common_tasks)


if __name__ == "__main__":
    import argparse

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--win-metric", type=str, default="dps", choices=["dps", "dps_norm"]
    )
    args = argparser.parse_args()
    data = read_json_files()
    model_winrates = compute_modelwise_winrates(data, args.win_metric)
    task_winrates = compute_taskwise_winrates(data, args.win_metric)
    stats = {}
    for model_id in data.keys():
        stats[model_id] = data[model_id]["summary"]
        stats[model_id]["model_win_rate"] = model_winrates[model_id]
        stats[model_id]["task_win_rate"] = task_winrates[model_id]

    dps_pairs = defaultdict(dict)
    for model_id in data.keys():
        for other_model_id in data.keys():
            if dps_pairs[other_model_id].get(model_id, None) is not None:
                dps_pairs[model_id][other_model_id] = (
                    dps_pairs[other_model_id][model_id][1],
                    dps_pairs[other_model_id][model_id][0],
                )
            else:
                dps_pairs[model_id][other_model_id] = compute_aligned_dps_pair(
                    data, model_id, other_model_id
                )
    stats["heatmap_data"] = dps_pairs

    with open(DST_PATH, "w") as f:
        json.dump(stats, f, indent=4)
