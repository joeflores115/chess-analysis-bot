# Chess Analysis Bot

This repository contains a chess analysis pipeline and a mirror-bot workflow that models player tendencies and common mistakes from game data.

## Pipeline runner

A single-entry orchestrator is available at:

- `src/run_pipeline.py`

It runs the pipeline in stage order and stops on the first error with a summary.

### Default full run

```bash
python /Users/mr.joseph/chess_analysis/src/run_pipeline.py
```

### Available stages

- `download`
- `parse`
- `analyze`
- `engine`
- `blunders`
- `profile`
- `mirror`
- `report`

List stages:

```bash
python /Users/mr.joseph/chess_analysis/src/run_pipeline.py --list-stages
```

### Run selected stages

Use explicit stage flags:

```bash
python /Users/mr.joseph/chess_analysis/src/run_pipeline.py --parse --analyze
```

Or use a comma-separated list:

```bash
python /Users/mr.joseph/chess_analysis/src/run_pipeline.py --stages engine,blunders,profile
```

### Safety and execution flags

- `--dry-run`: print what would run, without executing scripts
- `--skip-existing`: skip a stage when all expected outputs already exist

Example:

```bash
python /Users/mr.joseph/chess_analysis/src/run_pipeline.py --dry-run --skip-existing
```

## Notes

- Existing analysis scripts are orchestrated as-is; their internal logic is unchanged.
- `engine` and `mirror` stages require `stockfish` available in `PATH`.
