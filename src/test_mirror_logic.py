import unittest
from unittest.mock import MagicMock
import chess
import mirror_bot_core

class TestMirrorLogic(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "v2_blunder_profile": {
                "quiet_move_blunder": 0.1,
                "unsafe_capture": 0.1,
                "unsafe_king_move": 0.1,
                "endgame_conversion_collapse": 0.1,
                "kingside_weakening_move": 0.1,
                "pawn_structure_push_blunder": 0.1,
                "castling_blunder": 0.1,
            },
            "v2_blunder_profile_by_phase": {
                "opening": {
                    "quiet_move_blunder": 0.9,
                    "unsafe_capture": 0.0,
                    "unsafe_king_move": 0.0,
                    "endgame_conversion_collapse": 0.0,
                    "kingside_weakening_move": 0.0,
                    "pawn_structure_push_blunder": 0.0,
                    "castling_blunder": 0.0,
                },
                "endgame": {
                    "quiet_move_blunder": 0.0,
                    "unsafe_capture": 0.0,
                    "unsafe_king_move": 0.9,
                    "endgame_conversion_collapse": 0.0,
                    "kingside_weakening_move": 0.0,
                    "pawn_structure_push_blunder": 0.0,
                    "castling_blunder": 0.0,
                }
            },
            "bot_behavior_hints": {
                "play_opening_sensibly": False,
                "allow_quiet_move_mistakes": True,
            }
        }

    def test_score_move_candidate_phase_aware(self):
        board = MagicMock(spec=chess.Board)
        move = chess.Move.from_uci("e2e4")

        # In opening, quiet_move_blunder is 0.9
        board.fullmove_number = 5
        score_opening = mirror_bot_core.score_move_candidate(board, move, 0, self.profile)

        # In endgame, quiet_move_blunder is 0.0
        board.fullmove_number = 100
        board.piece_map.return_value = {i: None for i in range(5)}
        score_endgame = mirror_bot_core.score_move_candidate(board, move, 0, self.profile)

        # Bonuses should differ because of different v2 profiles
        self.assertNotEqual(score_opening["style_only_score"], score_endgame["style_only_score"])

    def test_pick_human_mode_move_phase_aware(self):
        candidates = [
            {
                "move": chess.Move.from_uci("e2e4"), # Quiet piece move
                "normalized_eval": 0.0,
                "style_only_score": 10.0,
                "features": {
                    "is_quiet_piece_move": True,
                    "is_capture": False,
                    "is_king_move": False,
                    "kingside_related": False,
                    "is_pawn_move": False,
                }
            },
            {
                "move": chess.Move.from_uci("e1d1"), # King move
                "normalized_eval": 0.0,
                "style_only_score": 10.0,
                "features": {
                    "is_quiet_piece_move": False,
                    "is_capture": False,
                    "is_king_move": True,
                    "kingside_related": False,
                    "is_pawn_move": False,
                }
            }
        ]

        # In opening, prefers quiet_move_blunder (e2e4)
        chosen_opening = mirror_bot_core.pick_human_mode_move(candidates, self.profile, "opening")
        self.assertEqual(chosen_opening["move"].uci(), "e2e4")

        # In endgame, prefers unsafe_king_move (e1d1)
        chosen_endgame = mirror_bot_core.pick_human_mode_move(candidates, self.profile, "endgame")
        self.assertEqual(chosen_endgame["move"].uci(), "e1d1")

if __name__ == "__main__":
    unittest.main()
