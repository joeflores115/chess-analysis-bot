import chess
import chess.pgn
import chess.engine
import pandas as pd
from paths import (
    ALL_GAMES_PGN,
    ENGINE_ANALYSIS_RECENT_300_CSV,
    ENGINE_GAME_SUMMARY_RECENT_300_CSV,
)

USERNAME = "katsmeow23"
ENGINE_PATH = "stockfish"

MAX_GAMES = 300
DEPTH = 10

# New: safer score handling
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

def phase_from_ply(ply_index, total_plies):
    if ply_index <= 20:
        return "Opening"
    elif ply_index <= max(40, total_plies - 20):
        return "Middlegame"
    else:
        return "Endgame"

games = []
with open(ALL_GAMES_PGN, "r", encoding="utf-8", errors="ignore") as f:
    while True:
        game = chess.pgn.read_game(f)
        if game is None:
            break
        games.append(game)

games = games[-MAX_GAMES:]
print(f"Loaded {len(games)} recent games for engine analysis.")

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

move_rows = []
game_rows = []

try:
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
            if result == "1-0":
                outcome = "Win"
            elif result == "0-1":
                outcome = "Loss"
            else:
                outcome = "Draw"
        elif black.lower() == USERNAME:
            my_color = chess.BLACK
            color_name = "Black"
            opponent = white
            if result == "0-1":
                outcome = "Win"
            elif result == "1-0":
                outcome = "Loss"
            else:
                outcome = "Draw"
        else:
            continue

        board = game.board()
        moves = list(game.mainline_moves())

        my_move_count = 0
        my_blunders = 0
        my_mistakes = 0
        my_inaccuracies = 0
        total_cp_loss = 0
        move_cp_losses = []

        for ply_index, move in enumerate(moves, start=1):
            side_to_move = board.turn
            phase = phase_from_ply(ply_index, len(moves))

            if side_to_move == my_color:
                my_move_count += 1

                info_before = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
                eval_before = score_to_cp(info_before["score"], my_color)

                played_move = move
                board.push(played_move)

                info_after = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
                eval_after = score_to_cp(info_after["score"], my_color)

                raw_cp_loss = max(0, eval_before - eval_after)
                cp_loss = min(raw_cp_loss, MAX_CP_LOSS_PER_MOVE)
                label = classify_loss(cp_loss)

                total_cp_loss += cp_loss
                move_cp_losses.append(cp_loss)

                if label == "Blunder":
                    my_blunders += 1
                elif label == "Mistake":
                    my_mistakes += 1
                elif label == "Inaccuracy":
                    my_inaccuracies += 1

                move_rows.append({
                    "GameIndex": game_idx,
                    "Date": date,
                    "Color": color_name,
                    "Opponent": opponent,
                    "Outcome": outcome,
                    "TimeControl": time_control,
                    "Termination": termination,
                    "PlyIndex": ply_index,
                    "Phase": phase,
                    "MoveUCI": played_move.uci(),
                    "EvalBeforeCP": eval_before,
                    "EvalAfterCP": eval_after,
                    "RawCPLoss": raw_cp_loss,
                    "CPLoss": cp_loss,
                    "MoveLabel": label,
                })
            else:
                board.push(move)

        avg_cp_loss = total_cp_loss / my_move_count if my_move_count else 0
        median_cp_loss = pd.Series(move_cp_losses).median() if move_cp_losses else 0

        game_rows.append({
            "GameIndex": game_idx,
            "Date": date,
            "Color": color_name,
            "Opponent": opponent,
            "Outcome": outcome,
            "TimeControl": time_control,
            "Termination": termination,
            "MyMoves": my_move_count,
            "Blunders": my_blunders,
            "Mistakes": my_mistakes,
            "Inaccuracies": my_inaccuracies,
            "TotalCPLoss": total_cp_loss,
            "AvgCPLoss": avg_cp_loss,
            "MedianMoveCPLoss": median_cp_loss,
        })

        print(
            f"Finished game {game_idx}/{len(games)} | "
            f"{date} | {color_name} | {outcome} | Avg CPLoss: {avg_cp_loss:.1f}"
        )

finally:
    engine.quit()

moves_df = pd.DataFrame(move_rows)
games_df = pd.DataFrame(game_rows)

moves_df.to_csv(ENGINE_ANALYSIS_RECENT_300_CSV, index=False)
games_df.to_csv(ENGINE_GAME_SUMMARY_RECENT_300_CSV, index=False)

print(f"\nSaved move-level analysis to: {ENGINE_ANALYSIS_RECENT_300_CSV}")
print(f"Saved game-level summary to: {ENGINE_GAME_SUMMARY_RECENT_300_CSV}")

if not games_df.empty:
    print("\n=== GAME-LEVEL SUMMARY ===")
    print(games_df[["AvgCPLoss", "MedianMoveCPLoss", "Blunders", "Mistakes", "Inaccuracies"]].describe())

    print("\n=== AVG CPL BY COLOR ===")
    print(games_df.groupby("Color")["AvgCPLoss"].mean())

    print("\n=== MEDIAN MOVE CPL BY COLOR ===")
    print(games_df.groupby("Color")["MedianMoveCPLoss"].mean())

    print("\n=== AVG CPL BY OUTCOME ===")
    print(games_df.groupby("Outcome")["AvgCPLoss"].mean())

    print("\n=== MEDIAN MOVE CPL BY OUTCOME ===")
    print(games_df.groupby("Outcome")["MedianMoveCPLoss"].mean())

if not moves_df.empty:
    print("\n=== MOVE LABEL COUNTS ===")
    print(moves_df["MoveLabel"].value_counts())

    print("\n=== MOVE LABELS BY PHASE ===")
    print(pd.crosstab(moves_df["Phase"], moves_df["MoveLabel"]))

    print("\n=== AVG CP LOSS BY PHASE ===")
    print(moves_df.groupby("Phase")["CPLoss"].mean())

    print("\n=== MEDIAN CP LOSS BY PHASE ===")
    print(moves_df.groupby("Phase")["CPLoss"].median())
