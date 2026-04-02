import json
import random
from typing import Optional

import pandas as pd
import chess
import chess.engine

from paths import REPORTS_DIR

PROFILE_FILE = REPORTS_DIR / "mirror_bot_profile_v1.json"
BLUNDER_FILE = REPORTS_DIR / "blunder_review_classified.csv"

BLUNDER_MODE_RATE = 0.35
EVAL_SCALE = 100.0
MULTIPV = 5
DEPTH = 10


def load_profile():
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_blunder_row(row_index: int):
    df = pd.read_csv(BLUNDER_FILE)
    if row_index < 0 or row_index >= len(df):
        raise IndexError(f"Row index {row_index} is out of range. File has {len(df)} rows.")
    return df.iloc[row_index]


def get_phase(board: chess.Board) -> str:
    move_count = board.fullmove_number

    if move_count <= 10:
        return "opening"

    piece_count = len(board.piece_map())
    if piece_count <= 10:
        return "endgame"

    return "middlegame"


def evaluate_move_features(board: chess.Board, move: chess.Move):
    piece = board.piece_at(move.from_square)
    piece_symbol = piece.symbol().lower() if piece else "?"

    to_file = chess.square_file(move.to_square)
    from_file = chess.square_file(move.from_square)

    kingside_related = from_file >= 5 or to_file >= 5
    is_capture = board.is_capture(move)
    is_castling = board.is_castling(move)
    is_quiet = (not is_capture) and (not is_castling)
    is_king_move = piece_symbol == "k"
    is_pawn_move = piece_symbol == "p"
    is_quiet_piece_move = is_quiet and (not is_pawn_move) and (not is_king_move)

    return {
        "piece_symbol": piece_symbol,
        "kingside_related": kingside_related,
        "is_capture": is_capture,
        "is_castling": is_castling,
        "is_quiet": is_quiet,
        "is_king_move": is_king_move,
        "is_pawn_move": is_pawn_move,
        "is_quiet_piece_move": is_quiet_piece_move,
    }


def score_move_candidate(board: chess.Board, move: chess.Move, eval_cp: int, profile: dict):
    phase = get_phase(board)
    normalized_eval = eval_cp / EVAL_SCALE

    hints = profile.get("bot_behavior_hints", {})
    v2 = profile.get("v2_blunder_profile", {})
    features = evaluate_move_features(board, move)

    penalties = []
    bonuses = []

    def add_penalty(name: str, amount: float):
        penalties.append((name, -amount))

    def add_bonus(name: str, amount: float):
        bonuses.append((name, amount))

    # Penalties
    if hints.get("play_opening_sensibly", False) and phase == "opening":
        add_bonus("opening_bonus", 20)

    if hints.get("prefer_errors_after_opening", False) and phase != "opening":
        add_penalty("later_phase_penalty", 5)

    if hints.get("allow_quiet_move_mistakes", False) and features["is_quiet"]:
        add_penalty("quiet_move_penalty", 100 * v2.get("quiet_move_blunder", 0))

    if hints.get("allow_unsafe_captures", False) and features["is_capture"]:
        add_penalty("unsafe_capture_penalty", 100 * v2.get("unsafe_capture", 0))

    if hints.get("treat_kingside_as_caution_zone", False) and features["kingside_related"]:
        add_penalty("kingside_penalty", 100 * v2.get("kingside_weakening_move", 0))

    if hints.get("allow_endgame_conversion_errors", False) and phase == "endgame":
        add_penalty("endgame_penalty", 100 * v2.get("endgame_conversion_collapse", 0))

    if hints.get("overweight_tactical_discipline_problems", False) and features["is_king_move"]:
        add_penalty("unsafe_king_move_penalty", 100 * v2.get("unsafe_king_move", 0))

    if features["is_castling"]:
        add_penalty("castling_penalty", 100 * v2.get("castling_blunder", 0))

    if features["is_pawn_move"]:
        add_penalty("pawn_move_penalty", 100 * v2.get("pawn_structure_push_blunder", 0))

    # More targeted self-like bonuses
    if phase != "opening":
        add_bonus("self_like_later_phase_bonus", 20)

    if features["is_quiet_piece_move"]:
        add_bonus("self_like_quiet_piece_bonus", 140 * v2.get("quiet_move_blunder", 0))

    if features["is_capture"]:
        add_bonus("self_like_capture_bonus", 140 * v2.get("unsafe_capture", 0))

    if features["is_king_move"]:
        add_bonus("self_like_king_move_bonus", 120 * v2.get("unsafe_king_move", 0))

    if features["kingside_related"]:
        add_bonus("self_like_kingside_bonus", 110 * v2.get("kingside_weakening_move", 0))

    if features["is_pawn_move"]:
        add_bonus("self_like_pawn_bonus", 70 * v2.get("pawn_structure_push_blunder", 0))

    if phase == "endgame":
        add_bonus("self_like_endgame_bonus", 120 * v2.get("endgame_conversion_collapse", 0))

    penalty_total = sum(v for _, v in penalties)
    bonus_total = sum(v for _, v in bonuses)
    style_only_score = penalty_total + bonus_total
    combined_score = normalized_eval + style_only_score

    return {
        "normalized_eval": normalized_eval,
        "style_only_score": style_only_score,
        "combined_score": combined_score,
        "features": features,
        "penalties": penalties,
        "bonuses": bonuses,
    }


def pick_human_mode_move(candidates):
    """
    Prefer specific buckets that match the user's most common blunder styles.
    Bucket priority:
    1. quiet piece moves
    2. captures
    3. king moves
    4. kingside-related moves
    5. pawn moves
    6. fallback: top style moves
    """
    quiet_piece_moves = [c for c in candidates if c["features"]["is_quiet_piece_move"]]
    captures = [c for c in candidates if c["features"]["is_capture"]]
    king_moves = [c for c in candidates if c["features"]["is_king_move"]]
    kingside_moves = [c for c in candidates if c["features"]["kingside_related"]]
    pawn_moves = [c for c in candidates if c["features"]["is_pawn_move"]]

    for bucket in [quiet_piece_moves, captures, king_moves, kingside_moves, pawn_moves]:
        if bucket:
            bucket_sorted = sorted(bucket, key=lambda x: x["style_only_score"], reverse=True)
            top_bucket = bucket_sorted[:3] if len(bucket_sorted) >= 3 else bucket_sorted
            return random.choice(top_bucket)

    fallback_sorted = sorted(candidates, key=lambda x: x["style_only_score"], reverse=True)
    top_fallback = fallback_sorted[:3] if len(fallback_sorted) >= 3 else fallback_sorted
    return random.choice(top_fallback)


def choose_mirror_move(board: chess.Board, engine, profile: dict):
    infos = engine.analyse(
        board,
        chess.engine.Limit(depth=DEPTH),
        multipv=MULTIPV
    )

    candidates = []
    for info in infos:
        pv = info.get("pv")
        if not pv:
            continue

        move = pv[0]
        score_obj = info["score"].pov(board.turn)
        eval_cp = score_obj.score(mate_score=10000)
        if eval_cp is None:
            eval_cp = 0

        score_data = score_move_candidate(board, move, eval_cp, profile)

        candidates.append({
            "move": move,
            "eval_cp": eval_cp,
            "normalized_eval": score_data["normalized_eval"],
            "style_only_score": score_data["style_only_score"],
            "combined_score": score_data["combined_score"],
            "features": score_data["features"],
            "penalties": score_data["penalties"],
            "bonuses": score_data["bonuses"],
        })

    engine_best = max(candidates, key=lambda x: x["eval_cp"]) if candidates else None
    candidates_sorted = sorted(candidates, key=lambda x: x["combined_score"], reverse=True)

    blunder_mode_used = False

    if random.random() < BLUNDER_MODE_RATE:
        chosen = pick_human_mode_move(candidates)
        blunder_mode_used = True
    else:
        top = candidates_sorted[:3] if len(candidates_sorted) >= 3 else candidates_sorted
        chosen = random.choice(top)

    return chosen, candidates_sorted, engine_best, blunder_mode_used


def move_to_san(board: chess.Board, move_uci: str):
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            return board.san(move)
    except Exception:
        pass
    return "(illegal or unavailable)"


def coaching_explanation(chosen, phase: str, blunder_mode_used: bool):
    features = chosen["features"]
    lines = []

    if blunder_mode_used:
        lines.append("Blunder mode was used here, so the bot leaned toward a move that fits your known mistake patterns more directly.")

    if phase != "opening":
        lines.append("This move appears after the opening, which matches your pattern of making more mistakes later in the game.")

    if features["is_quiet_piece_move"]:
        lines.append("This is a quiet piece move, which matches your biggest blunder category more closely than a generic quiet move.")

    if features["is_capture"]:
        lines.append("This is a capture, and your data shows that some of your captures fail tactically.")

    if features["is_king_move"]:
        lines.append("This is a king move, and king movement is one of your recurring danger areas.")

    if features["is_pawn_move"] and features["kingside_related"]:
        lines.append("This is a kingside pawn move, which matches another one of your known risk patterns.")

    if features["kingside_related"] and not features["is_pawn_move"]:
        lines.append("This move touches the kingside, which is a zone where many of your blunders cluster.")

    if phase == "endgame":
        lines.append("This position is in an endgame-like phase, where your conversion and stability are less reliable.")

    if not lines:
        lines.append("This move does not strongly trigger one of your biggest known blunder patterns.")

    return lines


def technical_explanation(chosen, blunder_mode_used: bool):
    lines = [
        f"normalized_eval: {chosen['normalized_eval']:.2f}",
        f"style_only_score: {chosen['style_only_score']:.2f}",
        f"combined_score: {chosen['combined_score']:.2f}",
        f"blunder_mode_used: {blunder_mode_used}",
    ]

    if chosen["penalties"]:
        lines.extend([f"{name}: {value:.2f}" for name, value in chosen["penalties"]])
    if chosen["bonuses"]:
        lines.extend([f"{name}: +{value:.2f}" for name, value in chosen["bonuses"]])

    return lines
