import chess
import chess.pgn
import chess.engine
import pandas as pd
from paths import ALL_GAMES_PGN

USERNAME = "katsmeow23"
ENGINE_PATH = "stockfish"

MAX_GAMES = 200
DEPTH = 10

RAPID_SET = {"600", "600+5", "900+10", "1800"}

MATE_SCORE_CP = 10000
MAX_CP_LOSS_PER_MOVE = 1000

def score_to_cp(score, perspective):
    pov = score.pov(perspective)
    cp = pov.score(mate_score=MATE_SCORE_CP)
    return 0 if cp is None else cp

def classify_loss(cp_loss):
    if cp_loss >= 300:
        return "Blunder"
    elif cp_loss >= 150:
        return "Mistake"
    elif cp_loss >= 50:
        return "Inaccuracy"
    else:
        return "OK"

def phase_from_ply(ply, total):
    if ply <= 20:
        return "Opening"
    elif ply <= max(40, total - 20):
        return "Middlegame"
    else:
        return "Endgame"

games = []
with open(ALL_GAMES_PGN, "r", encoding="utf-8", errors="ignore") as f:
    while True:
        g = chess.pgn.read_game(f)
        if g is None:
            break
        tc = g.headers.get("TimeControl", "")
        if tc in RAPID_SET:
            games.append(g)

games = games[-MAX_GAMES:]

print(f"Loaded {len(games)} recent RAPID games.")

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

move_rows = []
game_rows = []

try:
    for idx, game in enumerate(games, start=1):
        headers = game.headers
        white = headers.get("White", "")
        black = headers.get("Black", "")
        result = headers.get("Result", "")
        date = headers.get("Date", "")
        time_control = headers.get("TimeControl", "")

        if white.lower() == USERNAME:
            my_color = chess.WHITE
            color_name = "White"
            outcome = "Win" if result == "1-0" else "Loss" if result == "0-1" else "Draw"
        elif black.lower() == USERNAME:
            my_color = chess.BLACK
            color_name = "Black"
            outcome = "Win" if result == "0-1" else "Loss" if result == "1-0" else "Draw"
        else:
            continue

        board = game.board()
        moves = list(game.mainline_moves())

        my_moves = 0
        total_cp_loss = 0
        move_cp_losses = []
        blunders = mistakes = inaccuracies = 0

        for ply, move in enumerate(moves, start=1):
            if board.turn == my_color:
                my_moves += 1

                before = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
                eval_before = score_to_cp(before["score"], my_color)

                board.push(move)

                after = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
                eval_after = score_to_cp(after["score"], my_color)

                raw_cp_loss = max(0, eval_before - eval_after)
                cp_loss = min(raw_cp_loss, MAX_CP_LOSS_PER_MOVE)
                label = classify_loss(cp_loss)

                total_cp_loss += cp_loss
                move_cp_losses.append(cp_loss)

                if label == "Blunder":
                    blunders += 1
                elif label == "Mistake":
                    mistakes += 1
                elif label == "Inaccuracy":
                    inaccuracies += 1

                move_rows.append({
                    "Game": idx,
                    "Date": date,
                    "Color": color_name,
                    "Outcome": outcome,
                    "TimeControl": time_control,
                    "Phase": phase_from_ply(ply, len(moves)),
                    "RawCPLoss": raw_cp_loss,
                    "CPLoss": cp_loss,
                    "Label": label
                })
            else:
                board.push(move)

        avg_cp = total_cp_loss / my_moves if my_moves else 0
        median_cp = pd.Series(move_cp_losses).median() if move_cp_losses else 0

        game_rows.append({
            "Game": idx,
            "Date": date,
            "Outcome": outcome,
            "Color": color_name,
            "AvgCPLoss": avg_cp,
            "MedianMoveCPLoss": median_cp,
            "Blunders": blunders,
            "Mistakes": mistakes,
            "Inaccuracies": inaccuracies
        })

        print(f"{idx}/{len(games)} | {color_name} | {outcome} | CPL {avg_cp:.1f}")

finally:
    engine.quit()

moves_df = pd.DataFrame(move_rows)
games_df = pd.DataFrame(game_rows)

print("\n=== RAPID SUMMARY ===")
print(games_df[["AvgCPLoss", "MedianMoveCPLoss", "Blunders", "Mistakes", "Inaccuracies"]].describe())

print("\n=== AVG CPL BY PHASE ===")
print(moves_df.groupby("Phase")["CPLoss"].mean())

print("\n=== MEDIAN CPL BY PHASE ===")
print(moves_df.groupby("Phase")["CPLoss"].median())

print("\n=== AVG CPL BY OUTCOME ===")
print(games_df.groupby("Outcome")["AvgCPLoss"].mean())

print("\n=== MEDIAN MOVE CPL BY OUTCOME ===")
print(games_df.groupby("Outcome")["MedianMoveCPLoss"].mean())

print("\n=== MOVE LABELS BY PHASE ===")
print(pd.crosstab(moves_df["Phase"], moves_df["Label"]))
