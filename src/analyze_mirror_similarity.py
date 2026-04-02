import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "mirror_comparison_data.csv"

df = pd.read_csv(INPUT_FILE).copy()

print("=== OVERALL MIRROR SIMILARITY ===")
total = len(df)
mirror_engine = int(df["MirrorMatchesEngine"].sum())
mirror_original = int(df["MirrorMatchesOriginal"].sum())

print(f"Total rows: {total}")
print(f"Mirror matches engine: {mirror_engine}/{total} = {mirror_engine/total:.2%}")
print(f"Mirror matches original: {mirror_original}/{total} = {mirror_original/total:.2%}")

print("\n=== MIRROR MATCHES ORIGINAL BY BLUNDER CLASS ===")
by_class = (
    df.groupby("OriginalBlunderClass")["MirrorMatchesOriginal"]
    .agg(["count", "sum", "mean"])
    .sort_values("mean", ascending=False)
)
by_class["mean"] = by_class["mean"].map(lambda x: f"{x:.2%}")
print(by_class)

print("\n=== MIRROR MATCHES ENGINE BY BLUNDER CLASS ===")
by_class_engine = (
    df.groupby("OriginalBlunderClass")["MirrorMatchesEngine"]
    .agg(["count", "sum", "mean"])
    .sort_values("mean", ascending=False)
)
by_class_engine["mean"] = by_class_engine["mean"].map(lambda x: f"{x:.2%}")
print(by_class_engine)

print("\n=== MIRROR MATCHES ORIGINAL BY PHASE ===")
by_phase = (
    df.groupby("Phase")["MirrorMatchesOriginal"]
    .agg(["count", "sum", "mean"])
    .sort_values("mean", ascending=False)
)
by_phase["mean"] = by_phase["mean"].map(lambda x: f"{x:.2%}")
print(by_phase)

print("\n=== MIRROR MATCHES ENGINE BY PHASE ===")
by_phase_engine = (
    df.groupby("Phase")["MirrorMatchesEngine"]
    .agg(["count", "sum", "mean"])
    .sort_values("mean", ascending=False)
)
by_phase_engine["mean"] = by_phase_engine["mean"].map(lambda x: f"{x:.2%}")
print(by_phase_engine)

print("\n=== SAMPLE ROWS WHERE MIRROR MATCHED ORIGINAL ===")
matched_original = df[df["MirrorMatchesOriginal"] == True].copy()
if matched_original.empty:
    print("No rows matched original move.")
else:
    show_cols = [
        "RowIndex",
        "OriginalMoveSAN",
        "EngineBestMoveSAN",
        "MirrorMoveSAN",
        "OriginalBlunderClass",
        "Phase",
        "MirrorPenalties",
    ]
    print(matched_original[show_cols].head(10))

print("\n=== SAMPLE ROWS WHERE MIRROR MATCHED ENGINE BUT NOT ORIGINAL ===")
matched_engine_not_original = df[
    (df["MirrorMatchesEngine"] == True) & (df["MirrorMatchesOriginal"] == False)
].copy()

if matched_engine_not_original.empty:
    print("No such rows.")
else:
    show_cols = [
        "RowIndex",
        "OriginalMoveSAN",
        "EngineBestMoveSAN",
        "MirrorMoveSAN",
        "OriginalBlunderClass",
        "Phase",
        "MirrorPenalties",
    ]
    print(matched_engine_not_original[show_cols].head(10))
