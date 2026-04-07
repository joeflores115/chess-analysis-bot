import argparse
from datetime import datetime, timezone

import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "mirror_comparison_data.csv"
HISTORY_FILE = REPORTS_DIR / "experiment_history.csv"
UNSAFE_KING_MOVE_LABEL = "Unsafe king move"

HISTORY_COLUMNS = [
    "timestamp",
    "label",
    "overall_engine_matches",
    "overall_engine_total",
    "overall_engine_rate",
    "overall_original_matches",
    "overall_original_total",
    "overall_original_rate",
    "unsafe_king_engine_matches",
    "unsafe_king_engine_total",
    "unsafe_king_engine_rate",
    "unsafe_king_original_matches",
    "unsafe_king_original_total",
    "unsafe_king_original_rate",
]


def as_bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    normalized = (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )
    return normalized.isin({"true", "1", "yes", "y", "t"})


def safe_rate(matches: int, total: int):
    if total == 0:
        return None
    return matches / total


def compute_metrics(df: pd.DataFrame) -> dict:
    required_columns = [
        "MirrorMatchesEngine",
        "MirrorMatchesOriginal",
        "OriginalBlunderClass",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            "Missing required columns in mirror comparison CSV: "
            + ", ".join(missing_columns)
        )

    mirror_matches_engine = as_bool_series(df["MirrorMatchesEngine"])
    mirror_matches_original = as_bool_series(df["MirrorMatchesOriginal"])
    unsafe_mask = (
        df["OriginalBlunderClass"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq(UNSAFE_KING_MOVE_LABEL.casefold())
    )

    overall_total = len(df)
    unsafe_total = int(unsafe_mask.sum())

    overall_engine_matches = int(mirror_matches_engine.sum())
    overall_original_matches = int(mirror_matches_original.sum())
    unsafe_king_engine_matches = int((mirror_matches_engine & unsafe_mask).sum())
    unsafe_king_original_matches = int((mirror_matches_original & unsafe_mask).sum())

    return {
        "overall_engine_matches": overall_engine_matches,
        "overall_engine_total": overall_total,
        "overall_engine_rate": safe_rate(overall_engine_matches, overall_total),
        "overall_original_matches": overall_original_matches,
        "overall_original_total": overall_total,
        "overall_original_rate": safe_rate(overall_original_matches, overall_total),
        "unsafe_king_engine_matches": unsafe_king_engine_matches,
        "unsafe_king_engine_total": unsafe_total,
        "unsafe_king_engine_rate": safe_rate(unsafe_king_engine_matches, unsafe_total),
        "unsafe_king_original_matches": unsafe_king_original_matches,
        "unsafe_king_original_total": unsafe_total,
        "unsafe_king_original_rate": safe_rate(unsafe_king_original_matches, unsafe_total),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append mirror comparison experiment metrics to experiment_history.csv"
    )
    parser.add_argument(
        "--label",
        default="unlabeled",
        help="Experiment name/label for this run",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(INPUT_FILE).copy()

    metrics = compute_metrics(df)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        **metrics,
    }

    new_row_df = pd.DataFrame([row], columns=HISTORY_COLUMNS)

    if HISTORY_FILE.exists():
        history_df = pd.read_csv(HISTORY_FILE)
        missing_history_columns = [
            col for col in HISTORY_COLUMNS if col not in history_df.columns
        ]
        if missing_history_columns:
            raise ValueError(
                "Existing experiment history is missing required columns: "
                + ", ".join(missing_history_columns)
            )
        history_df = pd.concat([history_df, new_row_df], ignore_index=True)
    else:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history_df = new_row_df

    history_df = history_df[HISTORY_COLUMNS]
    history_df.to_csv(HISTORY_FILE, index=False)

    print(f"Appended experiment row to: {HISTORY_FILE}")
    print(new_row_df.to_string(index=False))


if __name__ == "__main__":
    main()