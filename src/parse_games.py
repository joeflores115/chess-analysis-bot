import chess.pgn
import pandas as pd
from paths import ALL_GAMES_PGN, GAMES_SUMMARY_CSV

username = "katsmeow23"

games_data = []

with open(ALL_GAMES_PGN, "r", encoding="utf-8", errors="ignore") as f:
    game_number = 0

    while True:
        game = chess.pgn.read_game(f)
        if game is None:
            break

        game_number += 1
        headers = game.headers

        white = headers.get("White", "")
        black = headers.get("Black", "")
        result = headers.get("Result", "")
        date = headers.get("Date", "")
        time_control = headers.get("TimeControl", "")
        eco = headers.get("ECO", "")
        opening = headers.get("Opening", "")
        termination = headers.get("Termination", "")
        site = headers.get("Site", "")
        white_elo = headers.get("WhiteElo", "")
        black_elo = headers.get("BlackElo", "")

        if white.lower() == username:
            color = "White"
            opponent = black
            my_elo = white_elo
            opp_elo = black_elo
            if result == "1-0":
                outcome = "Win"
            elif result == "0-1":
                outcome = "Loss"
            else:
                outcome = "Draw"
        elif black.lower() == username:
            color = "Black"
            opponent = white
            my_elo = black_elo
            opp_elo = white_elo
            if result == "0-1":
                outcome = "Win"
            elif result == "1-0":
                outcome = "Loss"
            else:
                outcome = "Draw"
        else:
            color = "Unknown"
            opponent = ""
            my_elo = ""
            opp_elo = ""
            outcome = "Unknown"

        moves = list(game.mainline_moves())
        num_moves = len(moves)

        games_data.append({
            "GameNumber": game_number,
            "Date": date,
            "Color": color,
            "Opponent": opponent,
            "Result": result,
            "Outcome": outcome,
            "MyElo": my_elo,
            "OpponentElo": opp_elo,
            "TimeControl": time_control,
            "ECO": eco,
            "Opening": opening,
            "Termination": termination,
            "Site": site,
            "NumPlies": num_moves
        })

df = pd.DataFrame(games_data)

df.to_csv(GAMES_SUMMARY_CSV, index=False)

print(f"Parsed {len(df)} games.")
print(f"Saved summary to: {GAMES_SUMMARY_CSV}")
print("\nFirst 5 rows:")
print(df.head())
