import pandas as pd
from paths import (
    GAMES_SUMMARY_RECENT_2000_CSV,
    GAMES_SUMMARY_ENRICHED_CSV,
)

df = pd.read_csv(GAMES_SUMMARY_RECENT_2000_CSV).copy()

print("Using last 2000 games only.")

print("\n=== BASIC SUMMARY ===")
print(f"Total games: {len(df)}")

print("\n=== OVERALL RESULTS ===")
print(df["Outcome"].value_counts(dropna=False))

print("\n=== RESULTS BY COLOR ===")
color_results = pd.crosstab(df["Color"], df["Outcome"])
print(color_results)

print("\n=== WIN RATE BY COLOR ===")
for color in ["White", "Black"]:
    subset = df[df["Color"] == color]
    total = len(subset)
    wins = (subset["Outcome"] == "Win").sum()
    losses = (subset["Outcome"] == "Loss").sum()
    draws = (subset["Outcome"] == "Draw").sum()
    if total > 0:
        print(
            f"{color}: {wins}/{total} wins = {wins/total:.2%}, "
            f"losses = {losses/total:.2%}, draws = {draws/total:.2%}"
        )

print("\n=== MOST COMMON TIME CONTROLS ===")
print(df["TimeControl"].value_counts(dropna=False).head(20))

print("\n=== GAME LENGTH STATS (plies) ===")
print(df["NumPlies"].describe())

print("\n=== AVERAGE GAME LENGTH BY OUTCOME ===")
print(df.groupby("Outcome")["NumPlies"].mean().sort_values())

print("\n=== AVERAGE GAME LENGTH BY COLOR ===")
print(df.groupby("Color")["NumPlies"].mean())

# Ratings
df["MyElo"] = pd.to_numeric(df["MyElo"], errors="coerce")
df["OpponentElo"] = pd.to_numeric(df["OpponentElo"], errors="coerce")
df["RatingDiff"] = df["MyElo"] - df["OpponentElo"]

print("\n=== RATING STATS ===")
print(df[["MyElo", "OpponentElo", "RatingDiff"]].describe())

bins = [-10000, -200, -100, 0, 100, 200, 10000]
labels = [
    "Opponent much higher rated",
    "Opponent higher rated",
    "Opponent slightly higher rated",
    "I am slightly higher rated",
    "I am higher rated",
    "I am much higher rated",
]
df["RatingBucket"] = pd.cut(df["RatingDiff"], bins=bins, labels=labels)

print("\n=== RESULTS BY RATING DIFFERENCE BUCKET ===")
bucket_table = pd.crosstab(df["RatingBucket"], df["Outcome"])
print(bucket_table)

print("\n=== WIN RATE BY RATING DIFFERENCE BUCKET ===")
for bucket in labels:
    subset = df[df["RatingBucket"] == bucket]
    total = len(subset)
    if total > 0:
        wins = (subset["Outcome"] == "Win").sum()
        losses = (subset["Outcome"] == "Loss").sum()
        draws = (subset["Outcome"] == "Draw").sum()
        print(
            f"{bucket}: wins = {wins/total:.2%}, "
            f"losses = {losses/total:.2%}, "
            f"draws = {draws/total:.2%} ({total} games)"
        )

username = "katsmeow23"

def normalize_termination(term: str) -> str:
    if pd.isna(term):
        return "Unknown"

    t = str(term).lower()

    if "drawn by stalemate" in t:
        return "Draw by stalemate"
    if "drawn by repetition" in t:
        return "Draw by repetition"
    if "drawn by insufficient material" in t:
        return "Draw by insufficient material"
    if "drawn by agreement" in t:
        return "Draw by agreement"
    if "timeout vs insufficient material" in t:
        return "Draw by timeout vs insufficient material"

    user_won = username in t and "won" in t

    if "won by checkmate" in t:
        return "Win by checkmate" if user_won else "Loss by checkmate"
    if "won by resignation" in t:
        return "Win by resignation" if user_won else "Loss by resignation"
    if "won on time" in t:
        return "Win on time" if user_won else "Loss on time"
    if "won - game abandoned" in t:
        return "Win by abandonment" if user_won else "Loss by abandonment"

    return "Other/Unknown"

df["TerminationNormalized"] = df["Termination"].apply(normalize_termination)

print("\n=== NORMALIZED TERMINATIONS ===")
print(df["TerminationNormalized"].value_counts(dropna=False))

df.to_csv(GAMES_SUMMARY_ENRICHED_CSV, index=False)
print(f"\nSaved enriched file as: {GAMES_SUMMARY_ENRICHED_CSV}")
