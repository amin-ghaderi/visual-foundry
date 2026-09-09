"""Simple CLI for the Memorial Design Pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from project import format_status, load_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline/run.py",
        description="Memorial Design Pipeline orchestrator.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-project", help="Create the next PXXX project folder.")
    create.add_argument("--template", default=None)
    create.add_argument("--id", dest="requested_id", default=None)

    new = sub.add_parser("new", help="Alias for create-project.")
    new.add_argument("requested_id", nargs="?", default=None)
    new.add_argument("--template", default=None)

    prep = sub.add_parser("prepare-image", help="Plan or run image preparation.")
    prep.add_argument("--project", required=True)
    prep.add_argument("--execute", action="store_true")

    validate = sub.add_parser("validate", help="Validate repo structure and an optional project.")
    validate.add_argument("--project", default=None)

    status = sub.add_parser("status", help="Print project status.")
    status.add_argument("--project", required=True)

    export = sub.add_parser("export", help="Show the deterministic Figma export path.")
    export.add_argument("--project", required=True)

    handoff = sub.add_parser("interpret-handoff", help="Interpret files in projects/PXXX/handoff/.")
    handoff.add_argument("--project", required=True)

    version = sub.add_parser("version", help="Show or bump current_version.")
    version.add_argument("--project", required=True)
    version.add_argument("--bump", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {"create-project", "new"}:
        from create_project import main as create_main

        extra: list[str] = []
        if getattr(args, "template", None):
            extra.extend(["--template", args.template])
        if getattr(args, "requested_id", None):
            extra.extend(["--id", args.requested_id])
        return create_main(extra)

    if args.command == "prepare-image":
        from prepare_image import main as prep_main

        extra = ["--project", args.project]
        if args.execute:
            extra.append("--execute")
        return prep_main(extra)

    if args.command == "validate":
        from validate import main as validate_main

        extra = ["--project", args.project] if args.project else []
        return validate_main(extra)

    if args.command == "status":
        try:
            print(format_status(load_project(args.project)))
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.command == "export":
        from export import main as export_main

        return export_main(["--project", args.project])

    if args.command == "interpret-handoff":
        from handoff import main as handoff_main

        return handoff_main(["--project", args.project])

    if args.command == "version":
        from version import main as version_main

        extra = ["--project", args.project]
        if args.bump:
            extra.append("--bump")
        return version_main(extra)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
