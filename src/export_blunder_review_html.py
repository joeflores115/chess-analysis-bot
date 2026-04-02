import pandas as pd
from urllib.parse import quote
from paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "blunder_review_classified.csv"
OUTPUT_FILE = REPORTS_DIR / "blunder_review.html"

df = pd.read_csv(INPUT_FILE).copy()

# Keep a manageable sample for review
sample_df = df.head(25).copy()

def lichess_analysis_link(fen: str) -> str:
    fen_encoded = quote(str(fen))
    return f"https://lichess.org/analysis/standard/{fen_encoded}"

html_parts = []
html_parts.append("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Blunder Review</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 24px;
            line-height: 1.4;
        }
        h1 {
            margin-bottom: 8px;
        }
        .card {
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .meta {
            margin-bottom: 8px;
        }
        .fen {
            font-family: monospace;
            background: #f5f5f5;
            padding: 8px;
            border-radius: 4px;
            word-break: break-all;
        }
        .label {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            background: #eee;
            margin-right: 6px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
""")

html_parts.append(f"<h1>Blunder Review</h1>")
html_parts.append(f"<p>Showing first {len(sample_df)} blunders from your classified review file.</p>")

for _, row in sample_df.iterrows():
    game_index = row.get("GameIndex", "")
    date = row.get("Date", "")
    color = row.get("Color", "")
    opponent = row.get("Opponent", "")
    outcome = row.get("Outcome", "")
    phase = row.get("Phase", "")
    move_number = row.get("MoveNumber", "")
    move_uci = row.get("MoveUCI", "")
    move_san = row.get("MoveSAN", "")
    cp_loss = row.get("CPLoss", "")
    fen = row.get("FENBefore", "")

    move_type = row.get("MoveTypeV1", "")
    san_type = row.get("SANTypeV1", "")
    zone = row.get("BoardZoneV1", "")
    phase_label = row.get("PhaseLabelV1", "")

    link = lichess_analysis_link(fen)

    html_parts.append('<div class="card">')
    html_parts.append(
        f'<div class="meta"><strong>Game {game_index}</strong> | {date} | {color} vs {opponent} | {outcome}</div>'
    )
    html_parts.append(
        f'<div class="meta"><strong>Phase:</strong> {phase} | <strong>Move:</strong> {move_number} | '
        f'<strong>Played:</strong> {move_san} ({move_uci}) | <strong>CPLoss:</strong> {cp_loss}</div>'
    )
    html_parts.append(
        f'<div class="meta">'
        f'<span class="label">{move_type}</span>'
        f'<span class="label">{san_type}</span>'
        f'<span class="label">{zone}</span>'
        f'<span class="label">{phase_label}</span>'
        f'</div>'
    )
    html_parts.append(f'<div class="fen">{fen}</div>')
    html_parts.append(f'<p><a href="{link}" target="_blank">Open this position in Lichess analysis</a></p>')
    html_parts.append('</div>')

html_parts.append("""
</body>
</html>
""")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("".join(html_parts))

print(f"Saved HTML review to: {OUTPUT_FILE}")
print(f"Included {len(sample_df)} blunders.")
