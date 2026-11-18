"""Run isolated Phase 3 validation experiments; evaluate test data only by opt-in."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bharatair.experiments.run import evaluate_test, run_experiment  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--run-id", help="Unique safe identifier under runs/ (generated if omitted)")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--resume", action="store_true", help="Resume only when run provenance matches exactly")
    parser.add_argument("--evaluate-test", action="store_true", help="Explicitly evaluate an already validation-complete run; requires --run-id")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    if args.evaluate_test:
        if not args.run_id:
            parser.error("--evaluate-test requires --run-id of a validation-complete run")
        if args.resume:
            parser.error("--resume cannot be combined with --evaluate-test")
        evaluate_test(args.run_id)
    else:
        run_experiment(run_id=args.run_id, device=args.device, resume=args.resume)


if __name__ == "__main__":
    main()
