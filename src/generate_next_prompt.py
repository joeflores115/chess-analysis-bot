import pandas as pd
from paths import REPORTS_DIR

HISTORY_FILE = REPORTS_DIR / "experiment_history.csv"
OUTPUT_FILE = REPORTS_DIR / "next_cline_prompt.md"

REQUIRED_COLUMNS = [
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


def as_text(value, fallback: str = "") -> str:
    if pd.isna(value):
        return fallback
    return str(value)


def as_int(value, fallback: int = 0) -> int:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return fallback
    return int(numeric)


def as_rate(value):
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return None
    return float(numeric)


def format_percent(rate) -> str:
    if rate is None:
        return "n/a"
    return f"{rate:.1%}"


def format_count_rate(matches: int, total: int, rate) -> str:
    return f"{matches}/{total} ({format_percent(rate)})"


def pct_point_delta(current_rate, previous_rate):
    if current_rate is None or previous_rate is None:
        return None
    return (current_rate - previous_rate) * 100.0


def format_delta(current_rate, previous_rate) -> str:
    delta = pct_point_delta(current_rate, previous_rate)
    if delta is None:
        return "n/a"
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f} pp"


def parse_history_row(row: pd.Series) -> dict:
    return {
        "timestamp": as_text(row.get("timestamp"), "unknown"),
        "label": as_text(row.get("label"), "unlabeled"),
        "overall_engine_matches": as_int(row.get("overall_engine_matches")),
        "overall_engine_total": as_int(row.get("overall_engine_total")),
        "overall_engine_rate": as_rate(row.get("overall_engine_rate")),
        "overall_original_matches": as_int(row.get("overall_original_matches")),
        "overall_original_total": as_int(row.get("overall_original_total")),
        "overall_original_rate": as_rate(row.get("overall_original_rate")),
        "unsafe_king_engine_matches": as_int(row.get("unsafe_king_engine_matches")),
        "unsafe_king_engine_total": as_int(row.get("unsafe_king_engine_total")),
        "unsafe_king_engine_rate": as_rate(row.get("unsafe_king_engine_rate")),
        "unsafe_king_original_matches": as_int(row.get("unsafe_king_original_matches")),
        "unsafe_king_original_total": as_int(row.get("unsafe_king_original_total")),
        "unsafe_king_original_rate": as_rate(row.get("unsafe_king_original_rate")),
    }


def choose_rule(latest: dict, previous: dict | None):
    if previous is None:
        unsafe_baseline_gap = None
        if latest["overall_original_rate"] is not None and latest["unsafe_king_original_rate"] is not None:
            unsafe_baseline_gap = (latest["overall_original_rate"] - latest["unsafe_king_original_rate"]) * 100.0

        if unsafe_baseline_gap is not None and unsafe_baseline_gap >= 8.0:
            return (
                "baseline_unsafe_king_focus",
                "Unsafe king original rate is at least 8 percentage points below overall original rate.",
            )

        if latest["overall_original_rate"] is not None and latest["overall_engine_rate"] is not None:
            original_vs_engine_gap = (latest["overall_engine_rate"] - latest["overall_original_rate"]) * 100.0
            if original_vs_engine_gap >= 8.0:
                return (
                    "baseline_human_likeness_focus",
                    "Overall original rate trails engine rate by at least 8 percentage points.",
                )

        return (
            "baseline_balanced_tuning",
            "Only one experiment row is available, so start with a small balanced tuning pass.",
        )

    overall_engine_delta = pct_point_delta(latest["overall_engine_rate"], previous["overall_engine_rate"])
    overall_original_delta = pct_point_delta(latest["overall_original_rate"], previous["overall_original_rate"])
    unsafe_engine_delta = pct_point_delta(latest["unsafe_king_engine_rate"], previous["unsafe_king_engine_rate"])
    unsafe_original_delta = pct_point_delta(latest["unsafe_king_original_rate"], previous["unsafe_king_original_rate"])

    unsafe_gap = None
    if latest["overall_original_rate"] is not None and latest["unsafe_king_original_rate"] is not None:
        unsafe_gap = (latest["overall_original_rate"] - latest["unsafe_king_original_rate"]) * 100.0

    if unsafe_original_delta is not None and unsafe_original_delta <= -2.0:
        return (
            "unsafe_king_recovery",
            "Unsafe king original rate dropped by at least 2 percentage points versus the previous run.",
        )

    if unsafe_gap is not None and unsafe_gap >= 10.0:
        return (
            "unsafe_king_recovery",
            "Unsafe king original rate trails overall original rate by at least 10 percentage points.",
        )

    if overall_original_delta is not None and overall_engine_delta is not None:
        if overall_original_delta <= -2.0 and overall_engine_delta >= 1.0:
            return (
                "recover_original_similarity",
                "Overall original rate dropped while engine alignment improved.",
            )
        if overall_engine_delta <= -2.0 and overall_original_delta >= 1.0:
            return (
                "recover_engine_alignment",
                "Engine alignment dropped while original similarity improved.",
            )

    tracked_deltas = [
        delta
        for delta in [overall_engine_delta, overall_original_delta, unsafe_engine_delta, unsafe_original_delta]
        if delta is not None
    ]
    if tracked_deltas and all(abs(delta) < 1.0 for delta in tracked_deltas):
        return (
            "small_exploration_step",
            "All tracked rates moved by less than 1 percentage point (stagnation).",
        )

    return (
        "balanced_increment",
        "Mixed movement across metrics; take a small targeted tuning step.",
    )


def build_suggested_prompt(rule_name: str) -> str:
    if rule_name in {"baseline_unsafe_king_focus", "unsafe_king_recovery"}:
        return (
            "Tune src/mirror_bot_core.py only (no pipeline/export changes).\n"
            "Goal: improve unsafe-king match rates without a redesign.\n"
            "1) In score_move_candidate, increase these multipliers by ~10-15%:\n"
            "   - quiet_king_move_penalty\n"
            "   - unsafe_king_move_penalty\n"
            "   - self_like_quiet_king_bonus\n"
            "   - self_like_king_move_bonus\n"
            "2) Keep BLUNDER_MODE_RATE unchanged for this pass.\n"
            "3) Keep non-king multipliers unchanged.\n"
            "4) Add brief inline comments documenting old -> new values."
        )

    if rule_name in {"baseline_human_likeness_focus", "recover_original_similarity"}:
        return (
            "Tune src/mirror_bot_core.py only (no pipeline/export changes).\n"
            "Goal: improve mirror-vs-original similarity.\n"
            "1) Increase BLUNDER_MODE_RATE by +0.05.\n"
            "2) Increase these self-like bonus multipliers by ~5-10%:\n"
            "   - self_like_quiet_piece_bonus\n"
            "   - self_like_capture_bonus\n"
            "3) Keep EVAL_WEIGHT_OPENING and EVAL_WEIGHT_NON_OPENING unchanged.\n"
            "4) Do not change king-specific multipliers in this iteration."
        )

    if rule_name == "recover_engine_alignment":
        return (
            "Tune src/mirror_bot_core.py only (no pipeline/export changes).\n"
            "Goal: recover engine alignment while preserving recent original-similarity gains.\n"
            "1) Decrease BLUNDER_MODE_RATE by -0.05.\n"
            "2) Increase EVAL_WEIGHT_NON_OPENING by +0.05.\n"
            "3) Keep per-feature style multipliers unchanged this round.\n"
            "4) Add brief inline comments documenting old -> new values."
        )

    if rule_name == "small_exploration_step":
        return (
            "Tune src/mirror_bot_core.py only (no pipeline/export changes).\n"
            "Goal: break stagnation with one minimal change.\n"
            "1) Adjust only BLUNDER_MODE_RATE by a small amount (±0.03).\n"
            "   - If overall_original_rate < overall_engine_rate, use +0.03\n"
            "   - Otherwise use -0.03\n"
            "2) Leave all evaluation weights and feature multipliers unchanged.\n"
            "3) Add a brief comment explaining why this single-parameter step was chosen."
        )

    return (
        "Tune src/mirror_bot_core.py only (no pipeline/export changes).\n"
        "Goal: make a small balanced iteration without redesigning the system.\n"
        "1) Increase self_like_quiet_piece_bonus and self_like_capture_bonus by ~5%.\n"
        "2) Keep BLUNDER_MODE_RATE and eval weights unchanged.\n"
        "3) Do not change king-specific multipliers in this pass.\n"
        "4) Add brief inline comments documenting old -> new values."
    )


def build_markdown(latest: dict, previous: dict | None, rule_name: str, reason: str, suggested_prompt: str) -> str:
    lines = [
        "# Next Cline Prompt Recommendation",
        "",
        "## Latest experiment",
        f"- timestamp: `{latest['timestamp']}`",
        f"- label: `{latest['label']}`",
        f"- overall engine: {format_count_rate(latest['overall_engine_matches'], latest['overall_engine_total'], latest['overall_engine_rate'])}",
        f"- overall original: {format_count_rate(latest['overall_original_matches'], latest['overall_original_total'], latest['overall_original_rate'])}",
        f"- unsafe king engine: {format_count_rate(latest['unsafe_king_engine_matches'], latest['unsafe_king_engine_total'], latest['unsafe_king_engine_rate'])}",
        f"- unsafe king original: {format_count_rate(latest['unsafe_king_original_matches'], latest['unsafe_king_original_total'], latest['unsafe_king_original_rate'])}",
    ]

    if previous is None:
        lines.extend([
            "",
            "## Baseline note",
            "- Only one experiment row exists, so this recommendation uses baseline-only logic.",
        ])
    else:
        lines.extend([
            "",
            "## Comparison vs previous",
            f"- previous label: `{previous['label']}`",
            f"- overall engine delta: {format_delta(latest['overall_engine_rate'], previous['overall_engine_rate'])}",
            f"- overall original delta: {format_delta(latest['overall_original_rate'], previous['overall_original_rate'])}",
            f"- unsafe king engine delta: {format_delta(latest['unsafe_king_engine_rate'], previous['unsafe_king_engine_rate'])}",
            f"- unsafe king original delta: {format_delta(latest['unsafe_king_original_rate'], previous['unsafe_king_original_rate'])}",
        ])

    lines.extend([
        "",
        "## Rule-based recommendation",
        f"- selected_rule: `{rule_name}`",
        f"- reason: {reason}",
        "",
        "## Suggested next Cline prompt",
        "```text",
        suggested_prompt,
        "```",
    ])

    return "\n".join(lines)


def main() -> None:
    if not HISTORY_FILE.exists():
        raise FileNotFoundError(f"Experiment history file not found: {HISTORY_FILE}")

    history_df = pd.read_csv(HISTORY_FILE).copy()

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in history_df.columns]
    if missing_columns:
        raise ValueError(
            "Experiment history is missing required columns: "
            + ", ".join(missing_columns)
        )

    if history_df.empty:
        raise ValueError("Experiment history has no rows to analyze.")

    latest = parse_history_row(history_df.iloc[-1])
    previous = parse_history_row(history_df.iloc[-2]) if len(history_df) >= 2 else None

    rule_name, reason = choose_rule(latest, previous)
    suggested_prompt = build_suggested_prompt(rule_name)
    markdown = build_markdown(latest, previous, rule_name, reason, suggested_prompt)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(markdown + "\n", encoding="utf-8")

    print(f"Saved next Cline prompt recommendation to: {OUTPUT_FILE}")
    print(f"Selected rule: {rule_name}")


if __name__ == "__main__":
    main()