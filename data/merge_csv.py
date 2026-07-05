from __future__ import annotations

import argparse
from pathlib import Path

from .csv_io import merge_decision_rows_csvs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge decision-row CSVs")
    parser.add_argument("inputs", nargs="+", type=Path, help="CSV files to merge")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="merged CSV path",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    sources = [path.expanduser().resolve() for path in args.inputs]
    for path in sources:
        if not path.is_file():
            raise SystemExit(f"input file does not exist: {path}")

    row_count = merge_decision_rows_csvs(sources, args.output)
    print(
        f"Merged {len(sources)} file(s), {row_count} decision(s) -> {args.output}",
        flush=True,
    )


if __name__ == "__main__":
    main()
