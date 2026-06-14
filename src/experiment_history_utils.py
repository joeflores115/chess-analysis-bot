import os
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

def append_to_experiment_history(
    history_file: Path,
    experiment_name: str,
    engine_matches: int,
    original_matches: int,
    total_rows: int,
    notes: str = ""
):
    """
    Appends benchmark results to the experiment history CSV.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    engine_match_pct = (engine_matches / total_rows * 100) if total_rows > 0 else 0
    original_match_pct = (original_matches / total_rows * 100) if total_rows > 0 else 0

    new_entry = {
        "ExperimentName": experiment_name,
        "Timestamp": timestamp,
        "MirrorMatchesEngine": engine_matches,
        "MirrorMatchesOriginal": original_matches,
        "EngineMatchPct": f"{engine_match_pct:.1f}%",
        "OriginalMatchPct": f"{original_match_pct:.1f}%",
        "Notes": notes
    }

    columns = [
        "ExperimentName",
        "Timestamp",
        "MirrorMatchesEngine",
        "MirrorMatchesOriginal",
        "EngineMatchPct",
        "OriginalMatchPct",
        "Notes"
    ]

    df_new = pd.DataFrame([new_entry], columns=columns)

    if history_file.exists():
        try:
            df_old = pd.read_csv(history_file)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
        except Exception as e:
            print(f"Warning: Could not read existing history file ({e}). Starting fresh.")
            df_combined = df_new
    else:
        history_file.parent.mkdir(parents=True, exist_ok=True)
        df_combined = df_new

    df_combined.to_csv(history_file, index=False)
    print(f"Logged experiment '{experiment_name}' to {history_file}")
