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


def win_rate_of_model(model_id: str, data: dict, metric: str):
    all_models = list(data.keys())
    other_models = [model for model in all_models if model != model_id]
    wins = 0
    all_rounds = 0
    for other_model in other_models:
        model1_wins, ties, model2_wins = model_compete(
            data[model_id]["eval"], data[other_model]["eval"], metric
        )
        wins += model1_wins + 0.5 * ties
        all_rounds += model1_wins + ties + model2_wins
    return wins / all_rounds


def compute_win_rates(data: dict, metric: str):
    win_rates = {}
    for model_id in data.keys():
        win_rates[model_id] = win_rate_of_model(model_id, data, metric)
    return win_rates


if __name__ == "__main__":
    import argparse

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--win-metric", type=str, default="dps", choices=["dps", "dps_norm"]
    )
    args = argparser.parse_args()
    data = read_json_files()
    win_rates = compute_win_rates(data, args.win_metric)
    stats = {}
    for model_id in data.keys():
        stats[model_id] = data[model_id]["summary"]
        stats[model_id]["win_rate"] = win_rates[model_id]
    with open(DST_PATH, "w") as f:
        json.dump(stats, f, indent=4)
