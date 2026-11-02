"""Command line interface for the structured data parser."""

import argparse
import json

from .core import DataError, convert, inspect_file, load_records


def build_parser():
    parser = argparse.ArgumentParser(description="Inspect, validate, and convert CSV/JSON/XML")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "validate", "preview"):
        command = commands.add_parser(name)
        command.add_argument("source")
    preview = commands.choices["preview"]
    preview.add_argument("--limit", type=int, default=5)
    conversion = commands.add_parser("convert")
    conversion.add_argument("source")
    conversion.add_argument("destination")
    conversion.add_argument("--overwrite", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            print(json.dumps(inspect_file(args.source), indent=2))
        elif args.command == "validate":
            rows = load_records(args.source)
            print(f"Valid: {len(rows)} record(s)")
        elif args.command == "preview":
            if args.limit < 0:
                raise DataError("--limit must be nonnegative")
            print(json.dumps(load_records(args.source)[:args.limit], indent=2))
        else:
            count = convert(args.source, args.destination, overwrite=args.overwrite)
            print(f"Converted {count} record(s) to {args.destination}")
    except DataError as exc:
        print(f"Error: {exc}", file=__import__("sys").stderr)
        return 1
    return 0
