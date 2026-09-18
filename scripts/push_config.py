#!/usr/bin/env python3
"""
push_config.py

Simulates an engineer pushing a configuration change to a network device,
the way it would happen against a real switch/router before QA re-validates
the change. This writes a small config file inside the target container.

Usage:
    python3 scripts/push_config.py --device device-1 --key hostname-desc --value "edge-router-01"
    python3 scripts/push_config.py --device device-1 --key hostname-desc --value "edge-router-01" --container-cmd docker
"""

import argparse
import subprocess
import sys

CONFIG_PATH = "/etc/lab-config.conf"


def push_config(device: str, key: str, value: str) -> bool:
    """Write a key=value line into the device's config file inside the container."""
    cmd = [
        "docker", "exec", device, "sh", "-c",
        f"echo '{key}={value}' > {CONFIG_PATH} && cat {CONFIG_PATH}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[FAILED] Could not push config to {device}: {result.stderr.strip()}", file=sys.stderr)
        return False

    print(f"[OK] Pushed config to {device}: {result.stdout.strip()}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Push a simulated config change to a lab device.")
    parser.add_argument("--device", required=True, help="Target container name, e.g. device-1")
    parser.add_argument("--key", required=True, help="Config key, e.g. hostname-desc")
    parser.add_argument("--value", required=True, help="Config value")
    args = parser.parse_args()

    success = push_config(args.device, args.key, args.value)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
