# Network Test Automation Framework

A Python/Pytest test automation suite built around a small Dockerized network
lab. It simulates a 3-device topology with real multi-hop routing, validates
connectivity/routing/configuration, automatically logs defects on failure,
and supports targeted retesting -- mirroring the QA workflow used for
validating IP switching platforms.

## Topology

```
device-1 (172.28.1.11) --- device-2 (172.28.1.12 / 172.28.2.12) --- device-3 (172.28.2.13)
        net-a (172.28.1.0/24)              net-b (172.28.2.0/24)
```

`device-1` and `device-3` are on **different subnets** and are not directly
connected. `device-2` sits on both subnets with IP forwarding enabled and
acts as the router between them -- so traffic between `device-1` and
`device-3` takes a real, routed, multi-hop path.

## What's tested

- **Connectivity** (`tests/test_connectivity.py`) -- direct links, multi-hop
  reachability in both directions, and a negative test confirming a removed
  route correctly breaks connectivity (proves the suite can detect real
  failures, not just confirm success).
- **Routing** (`tests/test_routing.py`) -- routing table contents, IP
  forwarding state on the router device, and interface configuration.
- **Configuration** (`tests/test_config.py`) -- simulates a config push to a
  device and validates the change was applied exactly as intended.

11 automated test cases total.

## Requirements

- Docker + Docker Compose (v2, i.e. `docker compose`, not the old
  `docker-compose` binary)
- Python 3.10+

## Setup

```bash
git clone <your-repo-url>
cd network-test-automation-framework
pip install -r requirements.txt
```

## Running the lab and tests

```bash
# 1. Start the virtual lab (3 containers, two subnets)
docker compose up -d

# 2. Give containers a few seconds to install tools and set up routes
sleep 10

# 3. Run the full test suite
pytest

# 4. Tear down the lab when done
docker compose down -v
```

To generate an HTML report:

```bash
pytest --html=logs/report.html --self-contained-html
```

## Defect logging

Any failed test is automatically written to `logs/defects.json` with the
test ID, expected/actual outcome, timestamp, and duration -- a structured
bug report generated the same way a real QA engineer would document one.

## Retesting after a fix

Instead of rerunning the entire suite, rerun only the tests that failed
last time:

```bash
python3 scripts/retest_failures.py
```

## Simulating a config push manually

```bash
python3 scripts/push_config.py --device device-1 --key hostname-desc --value "edge-router-01"
```

## CI/CD

`.github/workflows/ci.yml` runs the full lab + test suite on every push and
pull request to `main`, and uploads the defect log and HTML report as build
artifacts.

## Project structure

```
network-test-automation-framework/
├── docker-compose.yml          # 3-device lab topology
├── pytest.ini
├── requirements.txt
├── README.md
├── tests/
│   ├── conftest.py             # container exec helper + defect logging hook
│   ├── test_connectivity.py
│   ├── test_routing.py
│   └── test_config.py
├── scripts/
│   ├── push_config.py          # simulated config push
│   └── retest_failures.py      # targeted retest of failed tests
├── logs/                       # defects.json + HTML report written here
└── .github/workflows/ci.yml
```

## Why this project exists

Built to practice the real day-to-day workflow of QA/test automation for
networking and switching software: establishing a lab topology, writing
Python automation, executing test suites, documenting defects, and
retesting after fixes -- without requiring access to real switching
hardware.
