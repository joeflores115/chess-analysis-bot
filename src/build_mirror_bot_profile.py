import json
import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "blunder_review_classified.csv"
OUTPUT_FILE = REPORTS_DIR / "mirror_bot_profile_v1.json"

df = pd.read_csv(INPUT_FILE).copy()

total = len(df)

def share(mask):
    count = int(mask.sum())
    return round(count / total, 4) if total else 0.0

# V2 Mapping for reuse
v2_map = {
    "Quiet move blunder": "quiet_move_blunder",
    "Unsafe capture": "unsafe_capture",
    "Unsafe king move": "unsafe_king_move",
    "Endgame conversion/collapse": "endgame_conversion_collapse",
    "Kingside weakening move": "kingside_weakening_move",
    "Pawn structure / push blunder": "pawn_structure_push_blunder",
    "Castling blunder": "castling_blunder",
}

# Phase-specific profiles
phase_profile = {}
for phase_name in ["Opening", "Middlegame", "Endgame"]:
    phase_df = df[df["Phase"] == phase_name]
    phase_total = len(phase_df)

    def phase_share(mask):
        count = int(mask.sum())
        return round(count / phase_total, 4) if phase_total else 0.0

    phase_key = phase_name.lower()
    phase_profile[phase_key] = {
        v2_key: phase_share(phase_df["BlunderClassV2"] == v2_label)
        for v2_label, v2_key in v2_map.items()
    }

profile = {
    "profile_name": "KatsMeow23 Mirror Bot V1",
    "source": "blunder_review_classified.csv",
    "total_blunders_analyzed": int(total),

    "style_summary": {
        "opening_reliability": "mostly_reasonable",
        "error_timing": "later_not_earlier",
        "primary_risk_zone": "kingside",
        "main_problem_type": "quiet_unsafe_moves",
        "secondary_problem_type": "unsafe_captures",
        "endgame_reliability": "unstable_conversion",
    },

    "blunder_shares": {
        "piece_move_share": share(df["MoveTypeV1"] == "Piece move"),
        "pawn_move_share": share(df["MoveTypeV1"] == "Pawn move"),
        "castling_share": share(df["MoveTypeV1"] == "Castling"),

        "non_capture_share": share(df["SANTypeV1"] == "Non-capture"),
        "capture_share": share(df["SANTypeV1"] == "Capture"),
        "king_move_share": share(df["SANTypeV1"] == "King move"),

        "kingside_share": share(df["BoardZoneV1"] == "Kingside-related"),
        "queenside_share": share(df["BoardZoneV1"] == "Queenside-related"),
        "central_share": share(df["BoardZoneV1"] == "Central-related"),

        "opening_share": share(df["PhaseLabelV1"] == "Opening blunder"),
        "early_middlegame_share": share(df["PhaseLabelV1"] == "Early middlegame blunder"),
        "middlegame_share": share(df["PhaseLabelV1"] == "Middlegame blunder"),
        "endgame_share": share(df["PhaseLabelV1"] == "Endgame blunder"),
    },

    "v2_blunder_profile": {
        v2_key: share(df["BlunderClassV2"] == v2_label)
        for v2_label, v2_key in v2_map.items()
    },

    "v2_blunder_profile_by_phase": phase_profile,

    "bot_behavior_hints": {
        "play_opening_sensibly": True,
        "prefer_errors_after_opening": True,
        "allow_quiet_move_mistakes": True,
        "allow_unsafe_captures": True,
        "treat_kingside_as_caution_zone": True,
        "allow_endgame_conversion_errors": True,
        "overweight_tactical_discipline_problems": True,
    }
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(profile, f, indent=2)

print(f"Saved mirror bot profile to: {OUTPUT_FILE}")
print("\nProfile preview (subset):\n")
print(json.dumps({
    "v2_blunder_profile": profile["v2_blunder_profile"],
    "v2_blunder_profile_by_phase": profile["v2_blunder_profile_by_phase"]
}, indent=2))
