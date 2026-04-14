import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent))

from mirror_bot_core import pick_human_mode_move

def test_dynamic_prioritization():
    # Mock candidates
    candidates = [
        {
            "move": "e2e4", # quiet move
            "features": {
                "is_quiet_piece_move": True,
                "is_capture": False,
                "is_king_move": False,
                "kingside_related": False,
                "is_pawn_move": False
            },
            "style_only_score": 10
        },
        {
            "move": "Ke1d1", # king move
            "features": {
                "is_quiet_piece_move": False,
                "is_capture": False,
                "is_king_move": True,
                "kingside_related": False,
                "is_pawn_move": False
            },
            "style_only_score": 10
        }
    ]

    # Profile A: Heavy King move blundere
    profile_a = {
        "v2_blunder_profile": {
            "unsafe_king_move": 0.8,
            "quiet_move_blunder": 0.1
        }
    }

    # Profile B: Heavy Quiet move blunderer
    profile_b = {
        "v2_blunder_profile": {
            "unsafe_king_move": 0.1,
            "quiet_move_blunder": 0.8
        }
    }

    print("Testing Profile A (King move dominant)...")
    chosen_a = pick_human_mode_move(candidates, profile_a)
    print(f"Chosen move: {chosen_a['move']}")
    assert chosen_a['features']['is_king_move'] == True

    print("Testing Profile B (Quiet move dominant)...")
    chosen_b = pick_human_mode_move(candidates, profile_b)
    print(f"Chosen move: {chosen_b['move']}")
    assert chosen_b['features']['is_quiet_piece_move'] == True

    print("Verification successful: Bot prioritized different moves based on profile frequencies.")

if __name__ == "__main__":
    test_dynamic_prioritization()
