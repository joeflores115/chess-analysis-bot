import argparse
import subprocess
import sys
import pandas as pd
from pathlib import Path
from paths import REPORTS_DIR, SRC_DIR

def run_script(script_name, args=[]):
    cmd = [sys.executable, str(SRC_DIR / script_name)] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}:")
        print(result.stderr)
        sys.exit(1)
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Run a mirror-bot experiment.")
    parser.add_argument("--name", type=str, required=True, help="Name of the experiment")
    parser.add_argument("--notes", type=str, default="", help="Notes for the experiment")
    args = parser.parse_args()

    # 1. Run export_mirror_comparison_data.py
    # We pass the experiment name and notes so it logs automatically via our changes
    print(f"--- Starting Experiment: {args.name} ---")
    run_script("export_mirror_comparison_data.py", ["--experiment-name", args.name, "--notes", args.notes])

    # 2. Run analyze_mirror_similarity.py
    print("\n--- Running Similarity Analysis ---")
    analysis_output = run_script("analyze_mirror_similarity.py")
    print(analysis_output)

    print(f"\nExperiment '{args.name}' completed and logged to experiment_history.csv")

if __name__ == "__main__":
    main()
