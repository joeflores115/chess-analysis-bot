import requests
import time

username = "KatsMeow23"
archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(archives_url, headers=headers)

print("Status code:", response.status_code)
print("First 300 characters of response:")
print(response.text[:300])

response.raise_for_status()

data = response.json()
archives = data["archives"]

all_pgns = []

for archive_url in archives:
    print(f"Fetching {archive_url}")
import requests
import time

username = "KatsMeow23"
archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(archives_url, headers=headers)

print("Status code:", response.status_code)
print("First 300 characters of response:")
print(response.text[:300])

response.raise_for_status()

data = response.json()
archives = data["archives"]

all_pgns = []

for archive_url in archives:
    print(f"Fetching {archive_url}")
    r = requests.get(archive_url, headers=headers)
    print("  status:", r.status_code)
    r.raise_for_status()
    month_data = r.json()

    for game in month_data.get("games", []):
        if "pgn" in game:
            all_pgns.append(game["pgn"])

    time.sleep(1)

with open("all_games.pgn", "w", encoding="utf-8") as f:
    for pgn in all_pgns:
        f.write(pgn + "\n\n")

print(f"Done! Saved {len(all_pgns)} games to all_games.pgn")
