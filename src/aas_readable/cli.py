from __future__ import annotations

"""Command-line interface for exporting AAS and AASX context bundles."""

import argparse
import sys
from pathlib import Path

from .document import BatchExportSummary
from .exporter import export_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aas-readable",
        description="Export normalized AAS context from an AASX package, AAS JSON file, or directory of inputs.",
    )
    parser.add_argument("input_path", type=Path, help="Path to the input .aasx/.json file or a directory of inputs")
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
        choices=("markdown", "yaml", "json", "both", "all"),
        default="markdown",
        help="Output format to write. Use `all` for Markdown, YAML, and JSON.",
    )
    parser.add_argument(
        "--view",
        choices=("lossless", "agent", "brief", "review"),
        default="review",
        help="Document view to render. Defaults to review.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        summary = export_path(
            input_path=args.input_path,
            output_dir=args.output_dir,
            include=args.include,
            overwrite=args.overwrite,
            output_format=args.output,
            view=args.view,
        )
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    output_kinds = {
        "markdown": "Markdown",
        "yaml": "YAML",
        "json": "JSON",
        "both": "Markdown and YAML",
        "all": "Markdown, YAML, and JSON",
    }[args.output]
    if isinstance(summary, BatchExportSummary):
        print(
            f"Exported {summary.file_count} file(s) "
            f"covering {summary.exported_submodel_count} submodel(s) "
            f"from {summary.input_path} to {summary.output_dir} "
            f"as {output_kinds} using the {args.view} view"
        )
    else:
        print(
            f"Exported {summary.submodel_count} submodel(s) "
            f"across {summary.asset_shell_count} AAS object(s) "
            f"from {summary.input_path} to {summary.output_dir} "
            f"as {output_kinds} using the {args.view} view"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
