#!/usr/bin/env python3
"""greet.py — a simple CLI that greets one or more people by name."""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greet.py",
        description="Print a greeting for the given name(s).",
    )
    parser.add_argument(
        "name",
        nargs="+",
        help="One or more names of the people to greet.",
    )
    parser.add_argument(
        "--times",
        type=int,
        default=1,
        metavar="N",
        help="How many times to print each greeting (default: 1).",
    )
    parser.add_argument(
        "--greeting",
        default="Hello",
        metavar="WORD",
        help="The greeting word to use (default: Hello).",
    )
    parser.add_argument(
        "--shout",
        action="store_true",
        help="Print the greeting in uppercase.",
    )
    return parser


def greet(name: str, times: int, greeting: str, shout: bool) -> None:
    line = f"{greeting}, {name}!"
    if shout:
        line = line.upper()
    for _ in range(times):
        print(line)


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.times < 1:
        print("error: --times must be at least 1", file=sys.stderr)
        sys.exit(2)
    for nm in args.name:
        greet(nm, args.times, args.greeting, args.shout)
