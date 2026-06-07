import argparse
import subprocess
import sys
import os

# Ensure src is on sys.path if needed
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from paths import SRC_DIR

def run_script(script_name, args=[]):
    # Construct command to run from project root
    cmd = [sys.executable, str(SRC_DIR / script_name)] + args
    print(f"Running: {' '.join(cmd)}")
    # check=True will raise CalledProcessError if script fails
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="Run a mirror-bot experiment.")
    parser.add_argument("--name", type=str, required=True, help="Name of the experiment")
    parser.add_argument("--notes", type=str, default="", help="Notes for the experiment")
    args = parser.parse_args()

    print(f"\n--- Starting Experiment: {args.name} ---")

    # 1. Run export_mirror_comparison_data.py
    # We pass the experiment name and notes so it logs automatically
    export_args = ["--experiment-name", args.name, "--notes", args.notes]
    run_script("export_mirror_comparison_data.py", export_args)

    # 2. Run analyze_mirror_similarity.py
    print("\n--- Running Similarity Analysis ---")
    run_script("analyze_mirror_similarity.py")

    print(f"\nExperiment '{args.name}' completed and logged to experiment_history.csv")

if __name__ == "__main__":
    main()
