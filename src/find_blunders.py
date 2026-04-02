import pandas as pd
from paths import ENGINE_ANALYSIS_RECENT_300_CSV, REPORTS_DIR

df = pd.read_csv(ENGINE_ANALYSIS_RECENT_300_CSV)

print("Columns in engine file:")
print(list(df.columns))

# Filter blunders only
blunders = df[df["MoveLabel"] == "Blunder"].copy()

print(f"\nTotal blunders: {len(blunders)}")

cols = [
    "GameIndex",
    "Date",
    "Color",
    "Opponent",
    "Outcome",
    "TimeControl",
    "Phase",
    "PlyIndex",
    "MoveUCI",
    "EvalBeforeCP",
    "EvalAfterCP",
    "RawCPLoss",
    "CPLoss",
]

available_cols = [col for col in cols if col in blunders.columns]

print("\nFirst 20 blunders:")
print(blunders[available_cols].head(20))

output_file = REPORTS_DIR / "blunders_only.csv"
blunders.to_csv(output_file, index=False)

print(f"\nSaved blunders to: {output_file}")

print("\nBlunders by phase:")
print(blunders["Phase"].value_counts())

print("\nAverage CPLoss on blunders:")
print(blunders["CPLoss"].mean())

print("\nTop 10 blunder moves by frequency:")
print(blunders["MoveUCI"].value_counts().head(10))

print("\nBlunders by move type:")

def classify_move(move):
    if move in ["e1g1", "e8g8", "e1c1", "e8c8"]:
        return "Castling"
    elif move[1] == "2" or move[1] == "7":
        return "Pawn move"
    else:
        return "Piece move"

blunders["MoveType"] = blunders["MoveUCI"].apply(classify_move)

print(blunders["MoveType"].value_counts())
