#!/usr/bin/env python3
"""greet.py — a simple CLI that greets someone by name."""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greet.py",
        description="Print a greeting for the given name.",
    )
    parser.add_argument(
        "name",
        help="The name of the person to greet.",
    )
    parser.add_argument(
        "--times",
        type=int,
        default=1,
        metavar="N",
        help="How many times to print the greeting (default: 1).",
    )
    return parser


def greet(name: str, times: int) -> None:
    for _ in range(times):
        print(f"Hello, {name}!")


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.times < 1:
        print("error: --times must be at least 1", file=sys.stderr)
        sys.exit(1)
    greet(args.name, args.times)
