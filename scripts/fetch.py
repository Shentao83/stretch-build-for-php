#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from common import ROOT, fetch, verify_cache

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch or verify pinned historical inputs')
    parser.add_argument('--cache', type=Path, default=ROOT / 'downloads')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    (verify_cache if args.verify_only else fetch)(Path(os.path.realpath(str(args.cache))))
