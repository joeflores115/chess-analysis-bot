# Chess Bot Project Notes

**Current Location:** `/app`

**Active Python Environment:**
`source .venv/bin/activate.fish` (requires initialization)

**Core Mirror-Bot Files:**
- `src/mirror_bot_core.py`
- `src/mirror_bot_decision_demo.py`
- `src/export_mirror_comparison_data.py`
- `src/analyze_mirror_similarity.py`

**Current Benchmark Metrics:**
- Mirror matches engine: 7/50 = 14%
- Mirror matches original: 1/50 = 2%

**Important Lessons:**
- Checkpoint files (e.g., `mirror_bot_core_best_checkpoint.py`) may not represent the best historical version or the current intended logic. Always treat the main core files as the primary source of truth.
- The low engine match rate (14%) is a result of the high `BLUNDER_MODE_RATE` (55%) and top-3 selection randomness designed to mimic human error.
- The extremely low original match rate (2%) is largely due to the candidate search space being limited to the top 8 engine moves, while many human blunders are deeper errors.

**Next Recommended Backend Task:**
Improve imitation (original move matching) without significantly increasing the engine-match frequency. This could involve expanding the candidate search space or fine-tuning move bucket priorities based on player-specific blunder distributions.

**Commands to Rerun the Benchmark:**
```bash
source .venv/bin/activate.fish
python src/export_mirror_comparison_data.py
python src/analyze_mirror_similarity.py
```
