import chess
import chess.pgn
import pandas as pd
from paths import ALL_GAMES_PGN, ENGINE_ANALYSIS_RECENT_300_CSV, REPORTS_DIR

USERNAME = "katsmeow23"

# Load engine blunder rows
engine_df = pd.read_csv(ENGINE_ANALYSIS_RECENT_300_CSV)
blunders = engine_df[engine_df["MoveLabel"] == "Blunder"].copy()

# Keep only the keys we need for matching
blunder_keys = set(zip(blunders["GameIndex"], blunders["PlyIndex"]))

# Read the same last 300 games used by engine_analyze_recent.py
games = []
with open(ALL_GAMES_PGN, "r", encoding="utf-8", errors="ignore") as f:
    while True:
        game = chess.pgn.read_game(f)
        if game is None:
            break
        games.append(game)

games = games[-300:]

review_rows = []

for game_idx, game in enumerate(games, start=1):
    headers = game.headers
    white = headers.get("White", "")
    black = headers.get("Black", "")
    result = headers.get("Result", "")
    date = headers.get("Date", "")
    time_control = headers.get("TimeControl", "")
    termination = headers.get("Termination", "")

    if white.lower() == USERNAME:
        my_color = chess.WHITE
        color_name = "White"
        opponent = black
        outcome = "Win" if result == "1-0" else "Loss" if result == "0-1" else "Draw"
    elif black.lower() == USERNAME:
        my_color = chess.BLACK
        color_name = "Black"
        opponent = white
        outcome = "Win" if result == "0-1" else "Loss" if result == "1-0" else "Draw"
    else:
        continue

    board = game.board()
    moves = list(game.mainline_moves())

    for ply_index, move in enumerate(moves, start=1):
        key = (game_idx, ply_index)

        if board.turn == my_color and key in blunder_keys:
            fen_before = board.fen()
            san_move = board.san(move)
            move_number = board.fullmove_number
            side_to_move = "White" if board.turn == chess.WHITE else "Black"

            review_rows.append({
                "GameIndex": game_idx,
                "Date": date,
                "Color": color_name,
                "Opponent": opponent,
                "Outcome": outcome,
                "TimeControl": time_control,
                "Termination": termination,
                "PlyIndex": ply_index,
                "MoveNumber": move_number,
                "SideToMove": side_to_move,
                "MoveUCI": move.uci(),
                "MoveSAN": san_move,
                "FENBefore": fen_before,
            })

        board.push(move)

review_df = pd.DataFrame(review_rows)

# Merge back with existing engine blunder info
merged = blunders.merge(
    review_df,
    on=["GameIndex", "Date", "Color", "Opponent", "Outcome", "TimeControl", "Termination", "PlyIndex", "MoveUCI"],
    how="left"
)

output_file = REPORTS_DIR / "blunder_review.csv"
merged.to_csv(output_file, index=False)

print(f"Built review file with {len(merged)} blunders.")
print(f"Saved to: {output_file}")

print("\nFirst 10 rows:")
show_cols = [
    "GameIndex", "Date", "Color", "Opponent", "Outcome",
    "Phase", "PlyIndex", "MoveNumber", "MoveUCI", "MoveSAN", "CPLoss"
]
available_cols = [c for c in show_cols if c in merged.columns]
print(merged[available_cols].head(10))
