"""Run Phase 2 pipeline; default uses local raw files only."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bharatair.data.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="authenticate and acquire missing monthly files")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")
    result = run_pipeline(acquire=args.download)
    print(json.dumps({"canonical_observations": result["canonical_observation_count"], "indexed_source_rows_in_target_files": result["source_audit"]["indexed_source_rows_in_target_files"], "outputs": result["outputs"]}, indent=2))


if __name__ == "__main__":
    main()
