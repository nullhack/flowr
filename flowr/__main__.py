"""CLI entrypoint for flowr — invoked via `python -m flowr`."""

import argparse
import importlib.metadata


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    meta = importlib.metadata.metadata("flowr")
    parser = argparse.ArgumentParser(
        prog="flowr",
        description=meta["Summary"],
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"flowr {meta['Version']}",
    )
    return parser


def main() -> None:
    """Run the application."""
    build_parser().parse_args()


if __name__ == "__main__":
    main()
