import json
from pathlib import Path

def merge_json_files():
    data_dir = Path(__file__).parent
    data_dict = {}
    for path in data_dir.iterdir():
        if not path.name.endswith(".json") or path.name == "COMBINED-RESULTS.json":
            continue
        with open(path, "r") as f:
            data = json.load(f)["summary"]
            model_name = path.name.split("_")[0]
            data_dict[model_name] = data
    combined_results_path = data_dir / "COMBINED-RESULTS.json"
    with open(combined_results_path, "w") as f:
        json.dump(data_dict, f, indent=2)
        
merge_json_files()