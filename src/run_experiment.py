import argparse
import subprocess
import sys
from paths import SRC_DIR

def run_script(script_name, args=[]):
    cmd = [sys.executable, str(SRC_DIR / script_name)] + args
    print(f"Running: {' '.join(cmd)}")
    # We use check=True to stop if a script fails
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="Run a mirror-bot experiment.")
    parser.add_argument("--name", type=str, required=True, help="Name of the experiment")
    parser.add_argument("--notes", type=str, default="", help="Notes for the experiment")
    args = parser.parse_args()

    # 1. Run export_mirror_comparison_data.py
    # We pass the experiment name and notes so it logs automatically via our changes
    print(f"\n--- Starting Experiment: {args.name} ---")
    run_script("export_mirror_comparison_data.py", ["--experiment-name", args.name, "--notes", args.notes])

    # 2. Run analyze_mirror_similarity.py
    print("\n--- Running Similarity Analysis ---")
    run_script("analyze_mirror_similarity.py")

    print(f"\nExperiment '{args.name}' completed and logged to experiment_history.csv")

if __name__ == "__main__":
    main()
