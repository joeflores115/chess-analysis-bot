#!/usr/bin/env python3
"""
Single-entry runner for the chess analysis + mirror bot workflow.

Examples:
  python src/run_pipeline.py
  python src/run_pipeline.py --parse --analyze
  python src/run_pipeline.py --stages engine,blunders,profile
  python src/run_pipeline.py --dry-run --skip-existing
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Stage:
    name: str
    description: str
    scripts: tuple[str, ...]
    required_inputs: tuple[Path, ...]
    expected_outputs: tuple[Path, ...]


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ENGINE_DIR = OUTPUTS_DIR / "engine"
REPORTS_DIR = OUTPUTS_DIR / "reports"


STAGES: tuple[Stage, ...] = (
    Stage(
        name="download",
        description="Download all games PGN from Chess.com",
        scripts=("download_games.py",),
        required_inputs=(),
        expected_outputs=(RAW_DIR / "all_games.pgn",),
    ),
    Stage(
        name="parse",
        description="Parse PGN into game summary tables",
        scripts=("parse_games.py", "parse_recent_games.py"),
        required_inputs=(RAW_DIR / "all_games.pgn",),
        expected_outputs=(
            PROCESSED_DIR / "games_summary.csv",
            PROCESSED_DIR / "games_summary_recent_2000.csv",
        ),
    ),
    Stage(
        name="analyze",
        description="Generate descriptive analysis outputs",
        scripts=("analyze_summary.py", "analyze_by_time_control.py"),
        required_inputs=(PROCESSED_DIR / "games_summary_recent_2000.csv",),
        expected_outputs=(
            PROCESSED_DIR / "games_summary_enriched.csv",
            PROCESSED_DIR / "games_summary_recent_2000_with_time_category.csv",
        ),
    ),
    Stage(
        name="engine",
        description="Run engine analysis on recent games",
        scripts=("engine_analyze_recent.py",),
        required_inputs=(RAW_DIR / "all_games.pgn",),
        expected_outputs=(
            ENGINE_DIR / "engine_analysis_recent_300.csv",
            ENGINE_DIR / "engine_game_summary_recent_300.csv",
        ),
    ),
    Stage(
        name="blunders",
        description="Build, extract, and classify blunder review data",
        scripts=("find_blunders.py", "build_blunder_review.py", "classify_blunders.py"),
        required_inputs=(ENGINE_DIR / "engine_analysis_recent_300.csv",),
        expected_outputs=(
            REPORTS_DIR / "blunders_only.csv",
            REPORTS_DIR / "blunder_review.csv",
            REPORTS_DIR / "blunder_review_classified.csv",
        ),
    ),
    Stage(
        name="profile",
        description="Summarize tendencies and build mirror profile",
        scripts=("summarize_player_tendencies.py", "build_mirror_bot_profile.py"),
        required_inputs=(REPORTS_DIR / "blunder_review_classified.csv",),
        expected_outputs=(
            REPORTS_DIR / "player_tendency_summary.txt",
            REPORTS_DIR / "mirror_bot_profile_v1.json",
        ),
    ),
    Stage(
        name="mirror",
        description="Run mirror comparison and similarity analysis",
        scripts=("export_mirror_comparison_data.py", "analyze_mirror_similarity.py"),
        required_inputs=(
            REPORTS_DIR / "blunder_review_classified.csv",
            REPORTS_DIR / "mirror_bot_profile_v1.json",
        ),
        expected_outputs=(REPORTS_DIR / "mirror_comparison_data.csv",),
    ),
    Stage(
        name="report",
        description="Export HTML reports",
        scripts=("export_blunder_review_html.py", "export_mirror_comparison_html.py"),
        required_inputs=(
            REPORTS_DIR / "blunder_review_classified.csv",
            REPORTS_DIR / "mirror_comparison_data.csv",
        ),
        expected_outputs=(
            REPORTS_DIR / "blunder_review.html",
            REPORTS_DIR / "mirror_comparison_review.html",
        ),
    ),
)


STAGE_BY_NAME = {stage.name: stage for stage in STAGES}
DEFAULT_ORDER = [stage.name for stage in STAGES]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run chess analysis pipeline stages.")

    parser.add_argument(
        "--stages",
        type=str,
        default="",
        help="Comma-separated stage list. Available: " + ", ".join(DEFAULT_ORDER),
    )

    for stage_name in DEFAULT_ORDER:
        parser.add_argument(
            f"--{stage_name}",
            action="store_true",
            help=f"Run only/select stage: {stage_name}",
        )

    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing scripts.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip a stage if all expected outputs already exist.",
    )
    parser.add_argument("--list-stages", action="store_true", help="List stage names and exit.")

    return parser.parse_args()


def select_stages(args: argparse.Namespace) -> list[Stage]:
    selected: set[str] = set()

    if args.stages:
        names = [s.strip() for s in args.stages.split(",") if s.strip()]
        unknown = [name for name in names if name not in STAGE_BY_NAME]
        if unknown:
            raise ValueError(f"Unknown stage(s): {', '.join(unknown)}")
        selected.update(names)

    for stage_name in DEFAULT_ORDER:
        if getattr(args, stage_name):
            selected.add(stage_name)

    if not selected:
        selected = set(DEFAULT_ORDER)

    return [STAGE_BY_NAME[name] for name in DEFAULT_ORDER if name in selected]


def ensure_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def check_stockfish_if_needed(stages: list[Stage], dry_run: bool) -> None:
    if any(s.name in {"engine", "mirror"} for s in stages):
        if shutil.which("stockfish") is None:
            message = "Stockfish not found in PATH, but selected stages require it (engine/mirror)."
            if dry_run:
                print(f"[WARN] {message}")
                return
            raise RuntimeError(message)


def stage_should_skip(stage: Stage) -> bool:
    return bool(stage.expected_outputs) and all(path.exists() for path in stage.expected_outputs)


def verify_required_inputs(stage: Stage, dry_run: bool) -> None:
    missing = [str(path) for path in stage.required_inputs if not path.exists()]
    if missing:
        if dry_run:
            print(
                f"[WARN] Missing required input(s) for stage '{stage.name}' (dry-run only):\n  - "
                + "\n  - ".join(missing)
            )
            return
        raise FileNotFoundError(
            f"Missing required input(s) for stage '{stage.name}':\n  - " + "\n  - ".join(missing)
        )


def run_script(script_name: str, dry_run: bool) -> None:
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    if script_name == "download_games.py":
        cwd = RAW_DIR
    else:
        cwd = SRC_DIR

    cmd = [sys.executable, str(script_path)]
    print(f"    $ (cwd={cwd}) {' '.join(cmd)}")
    if not dry_run:
        subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> int:
    args = parse_args()

    if args.list_stages:
        print("Available stages:")
        for stage in STAGES:
            print(f"- {stage.name}: {stage.description}")
        return 0

    try:
        stages = select_stages(args)
        check_stockfish_if_needed(stages, dry_run=args.dry_run)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    ensure_dirs((RAW_DIR, PROCESSED_DIR, ENGINE_DIR, REPORTS_DIR))

    print("\n=== PIPELINE CONFIG ===")
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Python       : {sys.executable}")
    print(f"Dry run      : {args.dry_run}")
    print(f"Skip existing: {args.skip_existing}")
    print("Stages       : " + ", ".join(stage.name for stage in stages))

    started = time.time()
    summary: list[tuple[str, str, float]] = []
    failed_stage = None
    failure_message = ""

    for index, stage in enumerate(stages, start=1):
        stage_start = time.time()
        print(f"\n[{index}/{len(stages)}] Stage: {stage.name}")
        print(f"  Description: {stage.description}")

        try:
            if args.skip_existing and stage_should_skip(stage):
                elapsed = time.time() - stage_start
                summary.append((stage.name, "SKIPPED", elapsed))
                print("  Status     : SKIPPED (all expected outputs already exist)")
                continue

            verify_required_inputs(stage, dry_run=args.dry_run)

            for script_name in stage.scripts:
                print(f"  Running    : {script_name}")
                run_script(script_name, dry_run=args.dry_run)

            elapsed = time.time() - stage_start
            summary.append((stage.name, "OK", elapsed))
            print(f"  Status     : OK ({elapsed:.1f}s)")

        except subprocess.CalledProcessError as exc:
            elapsed = time.time() - stage_start
            summary.append((stage.name, "FAILED", elapsed))
            failed_stage = stage.name
            failure_message = (
                f"Script failed with non-zero exit code {exc.returncode} in stage '{stage.name}'."
            )
            print(f"  Status     : FAILED ({elapsed:.1f}s)")
            break
        except Exception as exc:
            elapsed = time.time() - stage_start
            summary.append((stage.name, "FAILED", elapsed))
            failed_stage = stage.name
            failure_message = str(exc)
            print(f"  Status     : FAILED ({elapsed:.1f}s)")
            break

    total_elapsed = time.time() - started

    print("\n=== PIPELINE SUMMARY ===")
    for name, status, elapsed in summary:
        print(f"- {name:<9} {status:<7} {elapsed:>6.1f}s")

    print(f"Total elapsed: {total_elapsed:.1f}s")

    if failed_stage:
        print("\nPipeline stopped on first error.")
        print(f"Failed stage : {failed_stage}")
        print(f"Reason       : {failure_message}")
        return 1

    print("\nPipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
