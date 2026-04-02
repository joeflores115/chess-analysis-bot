import pandas as pd
from paths import (
    GAMES_SUMMARY_RECENT_2000_CSV,
    GAMES_SUMMARY_RECENT_2000_WITH_TIME_CSV,
)

df = pd.read_csv(GAMES_SUMMARY_RECENT_2000_CSV).copy()

def classify_time_control(tc: str) -> str:
    tc = str(tc).strip()

    rapid_controls = {"600", "600+5", "900+10", "1800"}
    blitz_controls = {"180+2", "300+5", "300+2", "300", "180"}
    daily_controls = {"1/86400", "1/259200", "1/604800"}

    if tc in rapid_controls:
        return "Rapid"
    elif tc in blitz_controls:
        return "Blitz"
    elif tc in daily_controls:
        return "Daily"
    else:
        return "Other"

df["TimeCategory"] = df["TimeControl"].apply(classify_time_control)

print("\n=== GAMES BY TIME CATEGORY ===")
print(df["TimeCategory"].value_counts(dropna=False))

print("\n=== RESULTS BY TIME CATEGORY ===")
print(pd.crosstab(df["TimeCategory"], df["Outcome"]))

print("\n=== WIN RATE BY TIME CATEGORY ===")
for cat in ["Rapid", "Blitz", "Daily", "Other"]:
    subset = df[df["TimeCategory"] == cat]
    total = len(subset)
    if total > 0:
        wins = (subset["Outcome"] == "Win").sum()
        losses = (subset["Outcome"] == "Loss").sum()
        draws = (subset["Outcome"] == "Draw").sum()
        print(
            f"{cat}: wins = {wins/total:.2%}, "
            f"losses = {losses/total:.2%}, "
            f"draws = {draws/total:.2%} ({total} games)"
        )

print("\n=== AVERAGE GAME LENGTH BY TIME CATEGORY ===")
print(df.groupby("TimeCategory")["NumPlies"].mean())

print("\n=== COLOR RESULTS WITHIN EACH TIME CATEGORY ===")
for cat in ["Rapid", "Blitz", "Daily", "Other"]:
    subset = df[df["TimeCategory"] == cat]
    if len(subset) > 0:
        print(f"\n--- {cat} ---")
        print(pd.crosstab(subset["Color"], subset["Outcome"]))

df.to_csv(GAMES_SUMMARY_RECENT_2000_WITH_TIME_CSV, index=False)
print(f"\nSaved as: {GAMES_SUMMARY_RECENT_2000_WITH_TIME_CSV}")
