from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporter import export_input_to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aasx-md-exporter",
        description="Export submodels from an AASX package or AAS JSON file to Markdown files.",
    )
    parser.add_argument("input_path", type=Path, help="Path to the input .aasx or .json file")
    parser.add_argument("output_dir", type=Path, help="Directory where Markdown files will be written")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="SUBMODEL_NAME",
        help="Restrict export to one or more submodel names",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing into an existing output directory",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        summary = export_input_to_markdown(
            input_path=args.input_path,
            output_dir=args.output_dir,
            include=args.include,
            overwrite=args.overwrite,
        )
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"Exported {summary.submodel_count} submodel(s) "
        f"across {summary.asset_shell_count} AAS object(s) "
        f"from {summary.input_path} to {summary.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
