import pandas as pd
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "blunder_review_classified.csv"
OUTPUT_FILE = REPORTS_DIR / "player_tendency_summary.txt"

df = pd.read_csv(INPUT_FILE).copy()

total_blunders = len(df)

def pct(n):
    return f"{(100 * n / total_blunders):.1f}%" if total_blunders else "0.0%"

lines = []
lines.append("PLAYER TENDENCY SUMMARY")
lines.append("=" * 30)
lines.append(f"Total blunders analyzed: {total_blunders}")
lines.append("")

# V1 counts
piece_moves = int((df["MoveTypeV1"] == "Piece move").sum())
pawn_moves = int((df["MoveTypeV1"] == "Pawn move").sum())
castling_moves = int((df["MoveTypeV1"] == "Castling").sum())

non_capture = int((df["SANTypeV1"] == "Non-capture").sum())
capture = int((df["SANTypeV1"] == "Capture").sum())
king_moves = int((df["SANTypeV1"] == "King move").sum())
castling_san = int((df["SANTypeV1"] == "Castling").sum())

kingside = int((df["BoardZoneV1"] == "Kingside-related").sum())
queenside = int((df["BoardZoneV1"] == "Queenside-related").sum())
central = int((df["BoardZoneV1"] == "Central-related").sum())

opening = int((df["PhaseLabelV1"] == "Opening blunder").sum())
early_mg = int((df["PhaseLabelV1"] == "Early middlegame blunder").sum())
middlegame = int((df["PhaseLabelV1"] == "Middlegame blunder").sum())
endgame = int((df["PhaseLabelV1"] == "Endgame blunder").sum())

lines.append("1. MOVE TYPE PROFILE")
lines.append(f"- Piece move blunders: {piece_moves} ({pct(piece_moves)})")
lines.append(f"- Pawn move blunders: {pawn_moves} ({pct(pawn_moves)})")
lines.append(f"- Castling blunders: {castling_moves} ({pct(castling_moves)})")
lines.append("")

lines.append("2. ACTION PROFILE")
lines.append(f"- Non-capture blunders: {non_capture} ({pct(non_capture)})")
lines.append(f"- Capture blunders: {capture} ({pct(capture)})")
lines.append(f"- King move blunders: {king_moves} ({pct(king_moves)})")
lines.append(f"- Castling SAN blunders: {castling_san} ({pct(castling_san)})")
lines.append("")

lines.append("3. BOARD ZONE PROFILE")
lines.append(f"- Kingside-related blunders: {kingside} ({pct(kingside)})")
lines.append(f"- Queenside-related blunders: {queenside} ({pct(queenside)})")
lines.append(f"- Central-related blunders: {central} ({pct(central)})")
lines.append("")

lines.append("4. PHASE PROFILE")
lines.append(f"- Opening blunders: {opening} ({pct(opening)})")
lines.append(f"- Early middlegame blunders: {early_mg} ({pct(early_mg)})")
lines.append(f"- Middlegame blunders: {middlegame} ({pct(middlegame)})")
lines.append(f"- Endgame blunders: {endgame} ({pct(endgame)})")
lines.append("")

# V2 counts
v2_counts = df["BlunderClassV2"].value_counts()

lines.append("5. V2 BLUNDER PROFILE")
for label, count in v2_counts.items():
    lines.append(f"- {label}: {count} ({pct(int(count))})")
lines.append("")

# V2 by phase
lines.append("6. V2 BLUNDERS BY PHASE")
v2_phase = pd.crosstab(df["BlunderClassV2"], df["Phase"])
for label in v2_phase.index:
    row = v2_phase.loc[label]
    opening_count = int(row.get("Opening", 0))
    middlegame_count = int(row.get("Middlegame", 0))
    endgame_count = int(row.get("Endgame", 0))
    lines.append(
        f"- {label}: Opening {opening_count}, Middlegame {middlegame_count}, Endgame {endgame_count}"
    )
lines.append("")

# Automatic interpretation
lines.append("7. AUTOMATIC INTERPRETATION")

top_class = v2_counts.index[0] if len(v2_counts) else None
if top_class:
    lines.append(f"- Most common V2 blunder type: {top_class}.")

if "Quiet move blunder" in v2_counts.index and v2_counts["Quiet move blunder"] >= 150:
    lines.append("- Quiet move safety is a major weakness; many mistakes happen on normal-looking moves.")

if "Unsafe capture" in v2_counts.index and v2_counts["Unsafe capture"] >= 100:
    lines.append("- Captures need extra checking; forcing moves often fail tactically.")

if "Unsafe king move" in v2_counts.index and v2_counts["Unsafe king move"] >= 50:
    lines.append("- King movement decisions are a recurring danger area.")

if "Endgame conversion/collapse" in v2_counts.index and v2_counts["Endgame conversion/collapse"] >= 50:
    lines.append("- Endgame technique and conversion remain major training priorities.")

if "Kingside weakening move" in v2_counts.index and v2_counts["Kingside weakening move"] >= 40:
    lines.append("- Kingside pawn and structure changes are a meaningful source of self-inflicted problems.")

if piece_moves > pawn_moves:
    lines.append("- Unsafe piece moves remain a bigger issue than pawn pushes overall.")

if kingside > queenside and kingside > central:
    lines.append("- Blunders cluster heavily on the kingside, suggesting king safety and structure issues.")

if endgame > opening:
    lines.append("- Endgame mistakes are much more important than opening mistakes in your current profile.")

lines.append("")
lines.append("8. MIRROR-BOT PERSONALITY NOTES (V2)")
lines.append("- Bot should play mostly reasonable openings, with errors appearing later rather than early.")
lines.append("- Bot should sometimes make quiet but unsafe piece moves in middlegame positions.")
lines.append("- Bot should occasionally choose tactically flawed captures.")
lines.append("- Bot should show caution problems around kingside structure and king movement.")
lines.append("- Bot should have a recognizable tendency to mishandle some endgame conversions.")

report_text = "\n".join(lines)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)

print(report_text)
print(f"\nSaved summary to: {OUTPUT_FILE}")
