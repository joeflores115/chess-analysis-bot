from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data folders
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Output folders
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"
ENGINE_DIR = OUTPUTS_DIR / "engine"

# Main files
ALL_GAMES_PGN = RAW_DIR / "all_games.pgn"

GAMES_SUMMARY_CSV = PROCESSED_DIR / "games_summary.csv"
GAMES_SUMMARY_RECENT_2000_CSV = PROCESSED_DIR / "games_summary_recent_2000.csv"
GAMES_SUMMARY_RECENT_2000_WITH_TIME_CSV = PROCESSED_DIR / "games_summary_recent_2000_with_time_category.csv"
GAMES_SUMMARY_ENRICHED_CSV = PROCESSED_DIR / "games_summary_enriched.csv"

ENGINE_ANALYSIS_RECENT_300_CSV = ENGINE_DIR / "engine_analysis_recent_300.csv"
ENGINE_GAME_SUMMARY_RECENT_300_CSV = ENGINE_DIR / "engine_game_summary_recent_300.csv"
