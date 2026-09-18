"""
Shared pytest fixtures for the Network Test Automation Framework.

- run_in_container(): executes a command inside a running lab container
  via `docker exec` and returns (returncode, stdout, stderr).
- A pytest hook logs every failed test to logs/defects.json in a
  structured format (expected/actual/timestamp/etc).
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
DEFECT_LOG = LOG_DIR / "defects.json"

DEVICES = ["device-1", "device-2", "device-3"]


def run_in_container(container: str, command: str, timeout: int = 10):
    """
    Run a shell command inside a lab container using `docker exec`.

    Returns a tuple: (returncode, stdout, stderr)
    """
    full_cmd = ["docker", "exec", container, "sh", "-c", command]
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout}s"


def ping(from_container: str, target_ip: str, count: int = 2, timeout: int = 10):
    """Ping target_ip from inside from_container. Returns True if reachable."""
    rc, out, err = run_in_container(
        from_container, f"ping -c {count} -W 2 {target_ip}", timeout=timeout
    )
    return rc == 0, out, err


@pytest.fixture(scope="session", autouse=True)
def wait_for_lab():
    """
    Give containers a moment to finish their startup command (apk install +
    route setup) before tests start hitting them.
    """
    time.sleep(3)
    yield


# ---------------------------------------------------------------------------
# Automated defect logging: any failed test is written to logs/defects.json
# with expected/actual/reproduction info, mirroring a real QA bug report.
# ---------------------------------------------------------------------------

def _load_existing_log():
    if DEFECT_LOG.exists():
        try:
            return json.loads(DEFECT_LOG.read_text())
        except json.JSONDecodeError:
            return []
    return []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        entry = {
            "test_id": item.nodeid,
            "test_name": item.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "expected": "Test to pass (see assertion in test source for expected condition)",
            "actual": str(report.longrepr.reprcrash.message) if hasattr(report.longrepr, "reprcrash") else str(report.longrepr),
            "file": str(item.fspath),
            "duration_seconds": round(report.duration, 3),
        }

        existing = _load_existing_log()
        existing.append(entry)
        DEFECT_LOG.write_text(json.dumps(existing, indent=2))


@pytest.fixture(scope="session", autouse=True)
def clear_previous_log(request):
    """
    Clear the defect log at the start of a full run (not for targeted
    retest.py runs, which read the previous log on purpose).
    """
    if not request.config.getoption("--keep-log"):
        DEFECT_LOG.write_text("[]")
    yield


def pytest_addoption(parser):
    parser.addoption(
        "--keep-log",
        action="store_true",
        default=False,
        help="Do not clear logs/defects.json at the start of the run (used by retest_failures.py)",
    )
