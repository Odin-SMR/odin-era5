#!/bin/env python3
import json
import os
import subprocess
import sys


def get_git_root() -> str:
    path = os.getcwd()
    git_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=path
    )
    return git_root.decode("utf-8").strip()


sys.path.insert(0, get_git_root())

import argparse
from datetime import date, timedelta

from app.process.handler.process_file import lambda_handler


def valid_date(iso_formatted: str) -> date:
    try:
        valid_date = date.fromisoformat(iso_formatted)
    except ValueError:
        raise argparse.ArgumentTypeError("date must be iso-formatted (YYYY-MM-DD)")
    return valid_date


def main() -> None:
    parser = argparse.ArgumentParser(description="Start ERA5 pipeline")
    parser.add_argument(
        "-s", "--start", help="Start date YYYY-MM-DD", type=valid_date, required=True
    )
    parser.add_argument(
        "-e", "--end", help="End date YYYY-MM-DD", type=valid_date, required=True
    )
    args = parser.parse_args()
    current_date: date = args.start
    while current_date <= args.end:
        lambda_handler(json.dumps({"date": current_date}), None)
        current_date = current_date + timedelta(days=1)


if __name__ == "__main__":
    main()
