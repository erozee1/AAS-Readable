from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporter import export_input_to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aas-readable",
        description="Export submodels from an AASX package or AAS JSON file to Markdown and optional YAML files.",
    )
    parser.add_argument("input_path", type=Path, help="Path to the input .aasx or .json file")
    parser.add_argument("output_dir", type=Path, help="Directory where export files will be written")
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
    parser.add_argument(
        "--output",
        choices=("markdown", "yaml", "both"),
        default="markdown",
        help="Output format to write. Defaults to markdown.",
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
            output_format=args.output,
        )
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    output_kinds = {
        "markdown": "Markdown",
        "yaml": "YAML",
        "both": "Markdown and YAML",
    }[args.output]
    print(
        f"Exported {summary.submodel_count} submodel(s) "
        f"across {summary.asset_shell_count} AAS object(s) "
        f"from {summary.input_path} to {summary.output_dir} "
        f"as {output_kinds}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
