import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "blunder_review.csv"
OUTPUT_FILE = REPORTS_DIR / "blunder_review_classified.csv"

df = pd.read_csv(INPUT_FILE).copy()

def classify_move_type(move_uci: str) -> str:
    if pd.isna(move_uci):
        return "Unknown"

    move = str(move_uci).strip().lower()

    if move in {"e1g1", "e8g8", "e1c1", "e8c8"}:
        return "Castling"

    from_sq = move[:2]
    if len(from_sq) != 2:
        return "Unknown"

    rank = from_sq[1]
    if rank in {"2", "7"}:
        return "Pawn move"

    return "Piece move"

def classify_san_type(move_san: str) -> str:
    if pd.isna(move_san):
        return "Unknown"

    san = str(move_san).strip()

    if san in {"O-O", "O-O+", "O-O#", "O-O-O", "O-O-O+", "O-O-O#"}:
        return "Castling"
    if san.startswith("K"):
        return "King move"
    if "x" in san:
        return "Capture"

    return "Non-capture"

def classify_position_zone(move_uci: str) -> str:
    if pd.isna(move_uci):
        return "Unknown"

    move = str(move_uci).strip().lower()
    if len(move) < 4:
        return "Unknown"

    from_sq = move[:2]
    to_sq = move[2:4]

    king_side_files = {"f", "g", "h"}
    queen_side_files = {"a", "b", "c"}

    if from_sq[0] in king_side_files or to_sq[0] in king_side_files:
        return "Kingside-related"
    if from_sq[0] in queen_side_files or to_sq[0] in queen_side_files:
        return "Queenside-related"

    return "Central-related"

def classify_phase_risk(phase: str, move_number: float) -> str:
    if pd.isna(phase):
        return "Unknown"

    phase = str(phase)

    if phase == "Opening":
        return "Opening blunder"
    if phase == "Endgame":
        return "Endgame blunder"
    if pd.notna(move_number) and move_number <= 15:
        return "Early middlegame blunder"

    return "Middlegame blunder"

def classify_v2(row) -> str:
    move_type = row.get("MoveTypeV1", "")
    san_type = row.get("SANTypeV1", "")
    zone = row.get("BoardZoneV1", "")
    phase_label = row.get("PhaseLabelV1", "")
    move_uci = str(row.get("MoveUCI", "")).lower()
    cp_loss = row.get("CPLoss", 0)

    if move_uci in {"e1g1", "e8g8", "e1c1", "e8c8"}:
        return "Castling blunder"

    if san_type == "King move":
        return "Unsafe king move"

    if move_type == "Pawn move" and zone == "Kingside-related":
        return "Kingside weakening move"

    if san_type == "Capture":
        return "Unsafe capture"

    if phase_label == "Endgame blunder" and cp_loss >= 500:
        return "Endgame conversion/collapse"

    if move_type == "Piece move" and san_type == "Non-capture":
        return "Quiet move blunder"

    if move_type == "Piece move":
        return "General piece safety blunder"

    if move_type == "Pawn move":
        return "Pawn structure / push blunder"

    return "Other"

df["MoveTypeV1"] = df["MoveUCI"].apply(classify_move_type)
df["SANTypeV1"] = df["MoveSAN"].apply(classify_san_type)
df["BoardZoneV1"] = df["MoveUCI"].apply(classify_position_zone)
df["PhaseLabelV1"] = df.apply(
    lambda row: classify_phase_risk(row.get("Phase"), row.get("MoveNumber")),
    axis=1
)

df["BlunderClassV2"] = df.apply(classify_v2, axis=1)

df.to_csv(OUTPUT_FILE, index=False)

print(f"Saved classified blunders to: {OUTPUT_FILE}")

print("\n=== BlunderClassV2 ===")
print(df["BlunderClassV2"].value_counts())

print("\n=== BlunderClassV2 by Phase ===")
print(pd.crosstab(df["BlunderClassV2"], df["Phase"]))

print("\nFirst 20 V2 rows:")
show_cols = [
    "GameIndex", "Date", "Color", "Opponent", "Outcome",
    "Phase", "MoveNumber", "MoveUCI", "MoveSAN", "CPLoss",
    "BlunderClassV2"
]
print(df[show_cols].head(20))
