#!/usr/bin/env python3
"""
retest_failures.py

Reads logs/defects.json (written automatically by the pytest suite on
failure) and reruns ONLY those specific failed tests -- mirroring a real
QA "retest after defect resolution" workflow instead of rerunning the
entire suite every time.

Usage:
    python3 scripts/retest_failures.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFECT_LOG = ROOT / "logs" / "defects.json"


def load_failed_test_ids() -> list[str]:
    if not DEFECT_LOG.exists():
        print("No defect log found at logs/defects.json -- nothing to retest.")
        return []

    try:
        entries = json.loads(DEFECT_LOG.read_text())
    except json.JSONDecodeError:
        print("Defect log is empty or invalid JSON -- nothing to retest.")
        return []

    test_ids = sorted({entry["test_id"] for entry in entries})
    return test_ids


def main():
    test_ids = load_failed_test_ids()

    if not test_ids:
        print("No previously failed tests recorded. Nothing to retest.")
        sys.exit(0)

    print(f"Retesting {len(test_ids)} previously failed test(s):")
    for tid in test_ids:
        print(f"  - {tid}")
    print()

    # --keep-log ensures the defect log isn't wiped before this retest run,
    # so we still know which tests were originally failing. The normal
    # pytest hook in conftest.py will re-log anything that fails again.
    cmd = ["pytest", "-v", "--keep-log"] + test_ids
    result = subprocess.run(cmd, cwd=ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
