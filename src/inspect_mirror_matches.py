import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "mirror_comparison_data_best_checkpoint.csv"

df = pd.read_csv(INPUT_FILE).copy()

print("=== OVERALL COUNTS ===")
total = len(df)
matched_original = int(df["MirrorMatchesOriginal"].sum())
matched_engine = int(df["MirrorMatchesEngine"].sum())

print(f"Total rows: {total}")
print(f"Matched original: {matched_original}")
print(f"Matched engine: {matched_engine}")

print("\n=== ROWS WHERE MIRROR MATCHED ORIGINAL ===")
matched_orig_df = df[df["MirrorMatchesOriginal"] == True].copy()

if matched_orig_df.empty:
    print("No rows matched original.")
else:
    show_cols = [
        "RowIndex",
        "OriginalMoveSAN",
        "OriginalMoveUCI",
        "OriginalBlunderClass",
        "Phase",
        "MirrorMoveSAN",
        "MirrorMoveUCI",
        "MirrorQuietPiece",
        "MirrorCapture",
        "MirrorKingMove",
        "MirrorPawnMove",
        "MirrorKingsideRelated",
        "MirrorPenalties",
        "MirrorBonuses",
    ]
    print(matched_orig_df[show_cols].to_string(index=False))

print("\n=== COUNTS OF FEATURES WHEN MIRROR MATCHED ORIGINAL ===")
if matched_orig_df.empty:
    print("No rows to summarize.")
else:
    feature_cols = [
        "MirrorQuietPiece",
        "MirrorCapture",
        "MirrorKingMove",
        "MirrorPawnMove",
        "MirrorKingsideRelated",
    ]
    for col in feature_cols:
        print(f"{col}: {int(matched_orig_df[col].sum())}/{len(matched_orig_df)}")

print("\n=== ROWS WHERE MIRROR MATCHED ENGINE BUT NOT ORIGINAL ===")
matched_engine_not_orig = df[
    (df["MirrorMatchesEngine"] == True) & (df["MirrorMatchesOriginal"] == False)
].copy()

if matched_engine_not_orig.empty:
    print("No rows in this category.")
else:
    show_cols = [
        "RowIndex",
        "OriginalMoveSAN",
        "OriginalMoveUCI",
        "OriginalBlunderClass",
        "Phase",
        "EngineBestMoveSAN",
        "MirrorMoveSAN",
        "MirrorQuietPiece",
        "MirrorCapture",
        "MirrorKingMove",
        "MirrorPawnMove",
        "MirrorKingsideRelated",
        "MirrorPenalties",
        "MirrorBonuses",
    ]
    print(matched_engine_not_orig[show_cols].head(15).to_string(index=False))

print("\n=== FEATURE RATES: MATCHED ORIGINAL VS MATCHED ENGINE ===")

def feature_rate_text(frame, col):
    if len(frame) == 0:
        return "0/0 = n/a"
    return f"{int(frame[col].sum())}/{len(frame)} = {frame[col].mean():.2%}"

feature_cols = [
    "MirrorQuietPiece",
    "MirrorCapture",
    "MirrorKingMove",
    "MirrorPawnMove",
    "MirrorKingsideRelated",
]

for col in feature_cols:
    print(f"\n{col}")
    print(f"  matched original: {feature_rate_text(matched_orig_df, col)}")
    print(f"  matched engine  : {feature_rate_text(matched_engine_not_orig, col)}")

print("\n=== BLUNDER CLASS COUNTS IN MATCHED ORIGINAL ROWS ===")
if matched_orig_df.empty:
    print("No rows to summarize.")
else:
    print(matched_orig_df["OriginalBlunderClass"].value_counts())

print("\n=== PHASE COUNTS IN MATCHED ORIGINAL ROWS ===")
if matched_orig_df.empty:
    print("No rows to summarize.")
else:
    print(matched_orig_df["Phase"].value_counts())
