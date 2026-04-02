import sys
import chess
import chess.engine
from mirror_bot_core import (
    load_profile,
    load_blunder_row,
    get_phase,
    choose_mirror_move,
    move_to_san,
    coaching_explanation,
    technical_explanation,
)

ENGINE_PATH = "stockfish"

def main():
    profile = load_profile()
    source = "starting position"
    metadata = None

    if len(sys.argv) > 2 and sys.argv[1] == "--row":
        row_index = int(sys.argv[2])
        row = load_blunder_row(row_index)
        fen = row["FENBefore"]
        board = chess.Board(fen)
        source = f"blunder row {row_index}"
        metadata = row
    elif len(sys.argv) > 1:
        fen = " ".join(sys.argv[1:])
        board = chess.Board(fen)
        source = "custom FEN"
    else:
        board = chess.Board()

    with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
        chosen, candidates, engine_best, blunder_mode_used = choose_mirror_move(board, engine, profile)

    phase = get_phase(board)

    print("=== MIRROR BOT DECISION DEMO ===")
    print(f"Source: {source}")
    print(f"FEN: {board.fen()}")
    print(f"Side to move: {'White' if board.turn == chess.WHITE else 'Black'}")
    print(f"Phase: {phase}")
    print(f"Blunder mode used: {blunder_mode_used}")

    if metadata is not None:
        original_uci = metadata.get("MoveUCI", "")
        original_san = metadata.get("MoveSAN", "")
        original_class = metadata.get("BlunderClassV2", "")
        original_cp = metadata.get("CPLoss", "")

        print("\nBlunder row metadata:")
        print(f"- Date: {metadata.get('Date', '')}")
        print(f"- Color: {metadata.get('Color', '')}")
        print(f"- Opponent: {metadata.get('Opponent', '')}")
        print(f"- Outcome: {metadata.get('Outcome', '')}")
        print(f"- Original blunder move: {original_san} ({original_uci})")
        print(f"- Original blunder class: {original_class}")
        print(f"- Original CPLoss: {original_cp}")

        print("\nMove comparison:")
        print(f"- Original move: {original_san} ({original_uci})")
        if engine_best is not None:
            print(f"- Engine best move: {move_to_san(board, engine_best['move'].uci())} ({engine_best['move'].uci()}) | eval_cp={engine_best['eval_cp']}")
        print(
            f"- Mirror bot move: {move_to_san(board, chosen['move'].uci())} ({chosen['move'].uci()}) | "
            f"eval_cp={chosen['eval_cp']} | combined_score={chosen['combined_score']:.2f}"
        )

    else:
        print(f"\nChosen move: {chosen['move'].uci()}")
        print(f"Chosen eval_cp: {chosen['eval_cp']}")
        print(f"Chosen combined_score: {chosen['combined_score']:.2f}")

    print("\nShort coaching explanation:")
    for line in coaching_explanation(chosen, phase, blunder_mode_used):
        print(f"- {line}")

    print("\nTechnical explanation:")
    for line in technical_explanation(chosen, blunder_mode_used):
        print(f"- {line}")

    print("\nTop candidates:")
    for c in candidates[:5]:
        f = c["features"]
        penalty_text = ", ".join([f"{name}={value:.2f}" for name, value in c["penalties"]]) or "none"
        bonus_text = ", ".join([f"{name}=+{value:.2f}" for name, value in c["bonuses"]]) or "none"

        print(
            f"move={c['move'].uci()} | "
            f"eval_cp={c['eval_cp']} | "
            f"normalized_eval={c['normalized_eval']:.2f} | "
            f"style_only_score={c['style_only_score']:.2f} | "
            f"combined_score={c['combined_score']:.2f} | "
            f"quiet_piece={f['is_quiet_piece_move']} | "
            f"capture={f['is_capture']} | "
            f"king_move={f['is_king_move']} | "
            f"pawn_move={f['is_pawn_move']} | "
            f"kingside_related={f['kingside_related']} | "
            f"penalties=[{penalty_text}] | "
            f"bonuses=[{bonus_text}]"
        )

if __name__ == "__main__":
    main()
