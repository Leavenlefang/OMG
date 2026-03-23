#!/usr/bin/env python3
"""
run_daily.py — Entry point for the daily brief.

Usage:
  python3 run_daily.py           # fetch + store + send LINE brief
  python3 run_daily.py --fetch   # fetch & store only (no LINE)
  python3 run_daily.py --brief   # generate brief from stored data (no fetch)
  python3 run_daily.py --preview # print brief without sending to LINE
"""

import argparse
import sys
from pathlib import Path

# Allow running as a script: python3 biz/run_daily.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from biz.income import aggregator
from biz.brief import generator


def main():
    parser = argparse.ArgumentParser(description="Daily business brief")
    parser.add_argument("--fetch",   action="store_true", help="Fetch & store income data only")
    parser.add_argument("--brief",   action="store_true", help="Generate & send brief from stored data")
    parser.add_argument("--preview", action="store_true", help="Print brief without sending to LINE")
    args = parser.parse_args()

    fetch_only  = args.fetch
    brief_only  = args.brief
    preview     = args.preview

    # Default: do everything
    do_fetch = not brief_only
    do_send  = not fetch_only

    summaries = None

    if do_fetch:
        print("📡 Fetching income data...")
        summaries = aggregator.run()
        print()

    if do_send:
        if preview:
            print(generator.build(summaries=summaries))
        else:
            generator.send_brief(summaries=summaries)


if __name__ == "__main__":
    main()
