"""
Config push validation tests.

Mirrors a common real QA task: after a config change is pushed to a device,
verify the device's actual state reflects exactly what was intended.
"""

import sys
from pathlib import Path

from conftest import run_in_container

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from push_config import push_config, CONFIG_PATH  # noqa: E402


def test_config_push_is_applied_correctly():
    """
    Push a config value to device-1, then read it back directly from the
    container to confirm it matches exactly -- not just that the push
    command exited successfully.
    """
    key = "hostname-desc"
    value = "edge-router-01"

    pushed = push_config("device-1", key, value)
    assert pushed, "Config push command failed to execute against device-1."

    rc, out, err = run_in_container("device-1", f"cat {CONFIG_PATH}")
    assert rc == 0, f"Could not read back config file on device-1: {err}"
    assert out.strip() == f"{key}={value}", (
        f"Config mismatch on device-1.\nExpected: {key}={value}\nActual:   {out.strip()}"
    )


def test_config_push_overwrites_previous_value():
    """
    Pushing a second config value should fully overwrite the first --
    validates the config isn't silently appending or leaving stale values.
    """
    push_config("device-1", "hostname-desc", "first-value")
    push_config("device-1", "hostname-desc", "second-value")

    rc, out, err = run_in_container("device-1", f"cat {CONFIG_PATH}")
    assert rc == 0, f"Could not read back config file on device-1: {err}"
    assert out.strip() == "hostname-desc=second-value", (
        f"Expected only the latest config value to be present.\nActual: {out.strip()}"
    )
    assert "first-value" not in out, "Stale config value was not overwritten."
