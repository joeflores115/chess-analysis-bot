import os
import random
import pandas as pd
import chess
import chess.engine
from paths import REPORTS_DIR
from mirror_bot_core import (
    load_profile,
    get_phase,
    choose_mirror_move,
    move_to_san,
    coaching_explanation,
)

BLUNDER_FILE = REPORTS_DIR / "blunder_review_classified.csv"
OUTPUT_FILE = REPORTS_DIR / "mirror_comparison_data.csv"
ENGINE_PATH = "stockfish"

NUM_ROWS = 50
RANDOM_SEED = int(os.getenv("MIRROR_RANDOM_SEED", "20260403"))

def penalties_to_text(penalties):
    if not penalties:
        return "none"
    return "; ".join([f"{name}:{value:.2f}" for name, value in penalties])

def feature_bool(features, key):
    return bool(features.get(key, False))

def main():
    # Reproducible mirror-bot randomness for stable benchmark comparisons.
    random.seed(RANDOM_SEED)
    profile = load_profile()
    df = pd.read_csv(BLUNDER_FILE).head(NUM_ROWS).copy()

    rows = []

    with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
        for idx, row in df.iterrows():
            fen = row["FENBefore"]
            board = chess.Board(fen)
            phase = get_phase(board)

            chosen, candidates, engine_best, blunder_mode_used = choose_mirror_move(board, engine, profile)

            original_uci = row.get("MoveUCI", "")
            original_san = row.get("MoveSAN", "")
            original_class = row.get("BlunderClassV2", "")
            original_cp = row.get("CPLoss", "")

            engine_best_uci = engine_best["move"].uci() if engine_best else ""
            engine_best_san = move_to_san(board, engine_best_uci) if engine_best else ""
            engine_best_eval = engine_best["eval_cp"] if engine_best else ""

            mirror_uci = chosen["move"].uci()
            mirror_san = move_to_san(board, mirror_uci)
            mirror_eval = chosen["eval_cp"]
            mirror_combined_score = chosen["combined_score"]
            mirror_style_only_score = chosen["style_only_score"]

            rows.append({
                "RowIndex": idx,
                "Date": row.get("Date", ""),
                "Color": row.get("Color", ""),
                "Opponent": row.get("Opponent", ""),
                "Outcome": row.get("Outcome", ""),
                "Phase": phase,
                "FENBefore": fen,

                "OriginalMoveSAN": original_san,
                "OriginalMoveUCI": original_uci,
                "OriginalBlunderClass": original_class,
                "OriginalCPLoss": original_cp,

                "EngineBestMoveSAN": engine_best_san,
                "EngineBestMoveUCI": engine_best_uci,
                "EngineBestEvalCP": engine_best_eval,

                "MirrorMoveSAN": mirror_san,
                "MirrorMoveUCI": mirror_uci,
                "MirrorEvalCP": mirror_eval,
                "MirrorCombinedScore": mirror_combined_score,
                "MirrorStyleOnlyScore": mirror_style_only_score,

                "MirrorMatchesEngine": mirror_uci == engine_best_uci,
                "MirrorMatchesOriginal": mirror_uci == original_uci,
                "BlunderModeUsed": blunder_mode_used,

                "MirrorQuietPiece": feature_bool(chosen["features"], "is_quiet_piece_move"),
                "MirrorCapture": feature_bool(chosen["features"], "is_capture"),
                "MirrorKingMove": feature_bool(chosen["features"], "is_king_move"),
                "MirrorPawnMove": feature_bool(chosen["features"], "is_pawn_move"),
                "MirrorKingsideRelated": feature_bool(chosen["features"], "kingside_related"),

                "MirrorPenalties": penalties_to_text(chosen["penalties"]),
                "MirrorBonuses": penalties_to_text(chosen["bonuses"]),
                "MirrorCoachingExplanation": " | ".join(coaching_explanation(chosen, phase, blunder_mode_used)),
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved comparison data to: {OUTPUT_FILE}")
    print(f"Included {len(out_df)} rows.")

    if not out_df.empty:
        print("\n=== MATCH SUMMARY ===")
        print(f"Mirror matches engine: {int(out_df['MirrorMatchesEngine'].sum())}/{len(out_df)}")
        print(f"Mirror matches original: {int(out_df['MirrorMatchesOriginal'].sum())}/{len(out_df)}")

        print("\n=== FIRST 10 ROWS ===")
        show_cols = [
            "RowIndex",
            "OriginalMoveSAN",
            "EngineBestMoveSAN",
            "MirrorMoveSAN",
            "MirrorMatchesEngine",
            "MirrorMatchesOriginal",
            "OriginalBlunderClass",
            "MirrorPenalties",
        ]
        print(out_df[show_cols].head(10))

if __name__ == "__main__":
    main()
