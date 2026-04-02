import json
import random
import pandas as pd
import chess
import chess.engine
from urllib.parse import quote
from paths import REPORTS_DIR

PROFILE_FILE = REPORTS_DIR / "mirror_bot_profile_v1.json"
BLUNDER_FILE = REPORTS_DIR / "blunder_review_classified.csv"
OUTPUT_FILE = REPORTS_DIR / "mirror_comparison_review.html"
ENGINE_PATH = "stockfish"

MULTIPV = 5
DEPTH = 10
NUM_ROWS = 12

def load_profile():
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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

    return {
        "piece_symbol": piece_symbol,
        "kingside_related": kingside_related,
        "is_capture": is_capture,
        "is_castling": is_castling,
        "is_quiet": is_quiet,
        "is_king_move": is_king_move,
        "is_pawn_move": is_pawn_move,
    }

def score_move_candidate(board: chess.Board, move: chess.Move, eval_cp: int, profile: dict):
    phase = get_phase(board)
    score = eval_cp

    hints = profile.get("bot_behavior_hints", {})
    v2 = profile.get("v2_blunder_profile", {})
    features = evaluate_move_features(board, move)
    penalties = []

    def apply_penalty(name: str, amount: float):
        nonlocal score
        score -= amount
        penalties.append((name, -amount))

    if hints.get("play_opening_sensibly", False) and phase == "opening":
        score += 20
        penalties.append(("opening_bonus", 20))

    if hints.get("prefer_errors_after_opening", False) and phase != "opening":
        apply_penalty("later_phase_penalty", 5)

    if hints.get("allow_quiet_move_mistakes", False) and features["is_quiet"]:
        apply_penalty("quiet_move_penalty", 100 * v2.get("quiet_move_blunder", 0))

    if hints.get("allow_unsafe_captures", False) and features["is_capture"]:
        apply_penalty("unsafe_capture_penalty", 100 * v2.get("unsafe_capture", 0))

    if hints.get("treat_kingside_as_caution_zone", False) and features["kingside_related"]:
        apply_penalty("kingside_penalty", 100 * v2.get("kingside_weakening_move", 0))

    if hints.get("allow_endgame_conversion_errors", False) and phase == "endgame":
        apply_penalty("endgame_penalty", 100 * v2.get("endgame_conversion_collapse", 0))

    if hints.get("overweight_tactical_discipline_problems", False) and features["is_king_move"]:
        apply_penalty("unsafe_king_move_penalty", 100 * v2.get("unsafe_king_move", 0))

    if features["is_castling"]:
        apply_penalty("castling_penalty", 100 * v2.get("castling_blunder", 0))

    if features["is_pawn_move"]:
        apply_penalty("pawn_move_penalty", 100 * v2.get("pawn_structure_push_blunder", 0))

    return score, features, penalties

def choose_mirror_move(board: chess.Board, engine, profile: dict):
    infos = engine.analyse(board, chess.engine.Limit(depth=DEPTH), multipv=MULTIPV)

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

        style_score, features, penalties = score_move_candidate(board, move, eval_cp, profile)

        candidates.append({
            "move": move,
            "eval_cp": eval_cp,
            "style_score": style_score,
            "features": features,
            "penalties": penalties,
        })

    candidates.sort(key=lambda x: x["style_score"], reverse=True)
    top = candidates[:3] if len(candidates) >= 3 else candidates
    chosen = random.choice(top)
    engine_best = max(candidates, key=lambda x: x["eval_cp"]) if candidates else None
    return chosen, candidates, engine_best

def coaching_explanation(chosen, phase: str):
    features = chosen["features"]
    penalties = [name for name, _ in chosen["penalties"]]
    lines = []

    if phase != "opening":
        lines.append("This move appears after the opening, which matches your pattern of making more mistakes later in the game.")
    if features["is_quiet"]:
        lines.append("This is a quiet move, and quiet move safety is one of your biggest blunder patterns.")
    if features["is_capture"]:
        lines.append("This is a capture, and your data shows that some of your captures fail tactically.")
    if features["is_king_move"]:
        lines.append("This is a king move, and king movement is one of your recurring danger areas.")
    if features["is_pawn_move"] and features["kingside_related"]:
        lines.append("This is a kingside pawn move, which matches another one of your known risk patterns.")
    if features["kingside_related"] and not features["is_pawn_move"]:
        lines.append("This move touches the kingside, which is a zone where many of your blunders cluster.")
    if "endgame_penalty" in penalties:
        lines.append("This position is in an endgame phase, where your conversion and stability are less reliable.")
    if not lines:
        lines.append("This move does not strongly trigger one of your biggest known blunder patterns.")

    return lines

def move_to_san(board: chess.Board, move_uci: str):
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            return board.san(move)
    except Exception:
        pass
    return "(illegal or unavailable)"

def lichess_analysis_link(fen: str) -> str:
    return f"https://lichess.org/analysis/standard/{quote(str(fen))}"

def format_penalties(penalties):
    if not penalties:
        return ["No style penalties or bonuses were applied."]
    return [f"{name}: {value:.2f}" for name, value in penalties]

def feature_tags(features):
    tags = []
    if features["is_quiet"]:
        tags.append("quiet")
    if features["is_capture"]:
        tags.append("capture")
    if features["is_king_move"]:
        tags.append("king move")
    if features["is_pawn_move"]:
        tags.append("pawn move")
    if features["kingside_related"]:
        tags.append("kingside")
    if features["is_castling"]:
        tags.append("castling")
    return tags

def html_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def render_tag(tag, kind="default"):
    cls = f"tag {kind}"
    return f"<span class='{cls}'>{html_escape(tag)}</span>"

def main():
    profile = load_profile()
    df = pd.read_csv(BLUNDER_FILE).head(NUM_ROWS).copy()

    cards = []

    with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
        for idx, row in df.iterrows():
            fen = row["FENBefore"]
            board = chess.Board(fen)
            phase = get_phase(board)
            chosen, candidates, engine_best = choose_mirror_move(board, engine, profile)

            original_uci = row.get("MoveUCI", "")
            original_san = row.get("MoveSAN", "")
            original_class = row.get("BlunderClassV2", "")
            original_cp = row.get("CPLoss", "")

            engine_best_san = move_to_san(board, engine_best["move"].uci()) if engine_best else ""
            mirror_san = move_to_san(board, chosen["move"].uci())

            cards.append({
                "row_index": idx,
                "date": row.get("Date", ""),
                "color": row.get("Color", ""),
                "opponent": row.get("Opponent", ""),
                "outcome": row.get("Outcome", ""),
                "phase": phase,
                "fen": fen,
                "original_san": original_san,
                "original_uci": original_uci,
                "original_class": original_class,
                "original_cp": original_cp,
                "engine_best_san": engine_best_san,
                "engine_best_uci": engine_best["move"].uci() if engine_best else "",
                "engine_best_eval": engine_best["eval_cp"] if engine_best else "",
                "mirror_san": mirror_san,
                "mirror_uci": chosen["move"].uci(),
                "mirror_eval": chosen["eval_cp"],
                "mirror_style_score": chosen["style_score"],
                "coaching_lines": coaching_explanation(chosen, phase),
                "technical_lines": format_penalties(chosen["penalties"]),
                "top_candidates": candidates[:5],
                "lichess_link": lichess_analysis_link(fen),
            })

    html = []
    html.append("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Mirror Bot Comparison Review</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 24px;
    line-height: 1.5;
    background: #fafafa;
    color: #111;
}
h1 {
    margin-bottom: 8px;
}
p.subtitle {
    margin-top: 0;
    color: #444;
}
.card {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 20px;
    background: white;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.meta {
    margin-bottom: 10px;
    font-size: 1.05rem;
}
.fen {
    font-family: monospace;
    background: #f5f5f5;
    padding: 10px;
    border-radius: 6px;
    word-break: break-all;
    margin-top: 10px;
}
.box {
    background: #fcfcfc;
    border: 1px solid #e8e8e8;
    padding: 12px;
    border-radius: 8px;
    margin-top: 12px;
}
.tag {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: #ececec;
    margin-right: 6px;
    margin-bottom: 6px;
    font-size: 0.9em;
}
.tag.phase { background: #e8eefc; }
.tag.class { background: #f3e8fc; }
.tag.candidate { background: #eef6ea; }
.move-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 10px;
    margin-top: 8px;
}
.move-card {
    border: 1px solid #e2e2e2;
    border-radius: 8px;
    padding: 10px;
    background: #fff;
}
.move-title {
    font-weight: bold;
    font-size: 1.05rem;
}
.move-sub {
    color: #555;
    font-size: 0.92rem;
    margin-bottom: 6px;
}
ul {
    margin-top: 8px;
    margin-bottom: 0;
}
code {
    font-family: monospace;
}
.small {
    color: #555;
    font-size: 0.92rem;
}
a {
    color: #4b2ca3;
}
</style>
</head>
<body>
""")
    html.append(f"<h1>Mirror Bot Comparison Review</h1>")
    html.append(f"<p class='subtitle'>Showing first {len(cards)} blunder rows.</p>")

    for card in cards:
        html.append("<div class='card'>")
        html.append(
            f"<div class='meta'><strong>Row {card['row_index']}</strong> | {html_escape(card['date'])} | "
            f"{html_escape(card['color'])} vs {html_escape(card['opponent'])} | {html_escape(card['outcome'])}</div>"
        )
        html.append(
            render_tag(card["phase"], "phase") +
            render_tag(card["original_class"], "class")
        )

        html.append(f"<div class='fen'>{html_escape(card['fen'])}</div>")
        html.append(f"<p><a href='{card['lichess_link']}' target='_blank'>Open this position in Lichess analysis</a></p>")

        html.append("<div class='box'><strong>Move comparison</strong>")
        html.append("<div class='move-grid'>")

        html.append(
            f"<div class='move-card'>"
            f"<div class='move-title'>Original move: {html_escape(card['original_san'])}</div>"
            f"<div class='move-sub'>{html_escape(card['original_uci'])}</div>"
            f"<div class='small'>CPLoss: {html_escape(card['original_cp'])}</div>"
            f"</div>"
        )

        html.append(
            f"<div class='move-card'>"
            f"<div class='move-title'>Engine best: {html_escape(card['engine_best_san'])}</div>"
            f"<div class='move-sub'>{html_escape(card['engine_best_uci'])}</div>"
            f"<div class='small'>eval_cp: {html_escape(card['engine_best_eval'])}</div>"
            f"</div>"
        )

        html.append(
            f"<div class='move-card'>"
            f"<div class='move-title'>Mirror bot: {html_escape(card['mirror_san'])}</div>"
            f"<div class='move-sub'>{html_escape(card['mirror_uci'])}</div>"
            f"<div class='small'>eval_cp: {html_escape(card['mirror_eval'])} | style_score: {card['mirror_style_score']:.2f}</div>"
            f"</div>"
        )

        html.append("</div></div>")

        html.append("<div class='box'><strong>Short coaching explanation</strong><ul>")
        for line in card["coaching_lines"]:
            html.append(f"<li>{html_escape(line)}</li>")
        html.append("</ul></div>")

        html.append("<div class='box'><strong>Technical explanation</strong><ul>")
        for line in card["technical_lines"]:
            html.append(f"<li><code>{html_escape(line)}</code></li>")
        html.append("</ul></div>")

        html.append("<div class='box'><strong>Top candidates</strong>")
        for c in card["top_candidates"]:
            f = c["features"]
            san = move_to_san(chess.Board(card["fen"]), c["move"].uci())
            html.append("<div class='move-card' style='margin-top:10px;'>")
            html.append(f"<div class='move-title'>{html_escape(san)}</div>")
            html.append(f"<div class='move-sub'>{html_escape(c['move'].uci())}</div>")
            html.append(
                f"<div class='small'>eval_cp: {c['eval_cp']} | style_score: {c['style_score']:.2f}</div>"
            )

            tags = feature_tags(f)
            if tags:
                html.append("<div style='margin-top:8px;'>")
                for tag in tags:
                    html.append(render_tag(tag, "candidate"))
                html.append("</div>")

            penalty_lines = format_penalties(c["penalties"])
            html.append("<ul>")
            for pline in penalty_lines:
                html.append(f"<li><code>{html_escape(pline)}</code></li>")
            html.append("</ul>")

            html.append("</div>")
        html.append("</div>")

        html.append("</div>")

    html.append("</body></html>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(html))

    print(f"Saved HTML comparison review to: {OUTPUT_FILE}")
    print(f"Included {len(cards)} rows.")

if __name__ == "__main__":
    main()
