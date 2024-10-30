import json
import os
import zipfile

import tempdir
import wget

REPOQA_RESULT_PATH = "dev-results"
REPOQA_SCORES_PATH = "ntoken_16384-scores.zip"
OUTPUT_PATH = "results/repoqa"


def main():
    combined_results = {}
    zip_url = f"https://github.com/evalplus/repoqa/releases/download/{REPOQA_RESULT_PATH}/{REPOQA_SCORES_PATH}"

    with tempdir.TempDir() as tmpdir:
        zip_path = os.path.join(tmpdir, f"{REPOQA_SCORES_PATH}.zip")
        wget.download(zip_url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Extract all the contents into the specified directory
            zip_ref.extractall(tmpdir)

        for root, _, files in os.walk(tmpdir):
            for filename in files:
                if "SCORES" in filename:
                    file_path = os.path.join(root, filename)
                    with open(file_path, "r") as output_f:
                        data = json.load(output_f)
                        eval_name = list(data.keys())[0]
                        data[eval_name].pop("results")
                        combined_results[eval_name] = data[eval_name]

    with open(os.path.join(OUTPUT_PATH, "COMBINED-RESULTS.json"), "w") as f_out:
        json.dump(combined_results, f_out, indent=4)


if __name__ == "__main__":
    main()
