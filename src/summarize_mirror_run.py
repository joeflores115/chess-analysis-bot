import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "mirror_comparison_data.csv"
OUTPUT_FILE = REPORTS_DIR / "latest_experiment_summary.md"
UNSAFE_KING_MOVE_LABEL = "Unsafe king move"


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


def format_rate(label: str, matches: int, total: int) -> str:
    if total == 0:
        return f"- {label}: {matches}/{total} (n/a)"
    return f"- {label}: {matches}/{total} ({matches / total:.1%})"


def main() -> None:
    df = pd.read_csv(INPUT_FILE).copy()

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

    total_rows = len(df)
    unsafe_total = int(unsafe_mask.sum())

    overall_engine_matches = int(mirror_matches_engine.sum())
    overall_original_matches = int(mirror_matches_original.sum())
    unsafe_engine_matches = int((mirror_matches_engine & unsafe_mask).sum())
    unsafe_original_matches = int((mirror_matches_original & unsafe_mask).sum())

    summary_lines = [
        "# Latest Experiment Summary",
        "",
        f"Source: `{INPUT_FILE}`",
        f"Total rows: {total_rows}",
        f"Unsafe king move rows: {unsafe_total}",
        "",
        "## Mirror match rates",
        format_rate("Overall mirror matches engine", overall_engine_matches, total_rows),
        format_rate("Overall mirror matches original", overall_original_matches, total_rows),
        format_rate(
            "Unsafe king move mirror matches engine",
            unsafe_engine_matches,
            unsafe_total,
        ),
        format_rate(
            "Unsafe king move mirror matches original",
            unsafe_original_matches,
            unsafe_total,
        ),
    ]
    summary_text = "\n".join(summary_lines)

    print(summary_text)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(summary_text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()