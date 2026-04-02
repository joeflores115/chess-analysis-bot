import chess.pgn
import pandas as pd
from paths import ALL_GAMES_PGN, GAMES_SUMMARY_RECENT_2000_CSV

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
        num_plies = len(moves)

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
            "NumPlies": num_plies
        })

df = pd.DataFrame(games_data)

recent_df = df.tail(2000).copy()
recent_df.to_csv(GAMES_SUMMARY_RECENT_2000_CSV, index=False)

print(f"Parsed {len(df)} total games.")
print(f"Saved last {len(recent_df)} games to: {GAMES_SUMMARY_RECENT_2000_CSV}")

print("\nDate range of recent sample:")
print("First date:", recent_df.iloc[0]["Date"])
print("Last date:", recent_df.iloc[-1]["Date"])
