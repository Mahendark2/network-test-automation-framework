"""
Routing-table and IP-forwarding validation tests.

These check the actual network state on each device (not just whether a
ping succeeds), which is what real QA validation of a routed/switched
platform looks like -- confirming the *configuration* is correct, not only
the *symptom*.
"""

from conftest import run_in_container


def test_device1_has_route_to_device3_subnet():
    """device-1's routing table must contain a route to device-3's subnet."""
    rc, out, err = run_in_container("device-1", "ip route show")
    assert rc == 0, f"Failed to read routing table on device-1: {err}"
    assert "172.28.2.0/24" in out, (
        f"device-1 is missing the expected route to 172.28.2.0/24. "
        f"Routing table:\n{out}"
    )


def test_device3_has_route_to_device1_subnet():
    """device-3's routing table must contain a route to device-1's subnet."""
    rc, out, err = run_in_container("device-3", "ip route show")
    assert rc == 0, f"Failed to read routing table on device-3: {err}"
    assert "172.28.1.0/24" in out, (
        f"device-3 is missing the expected route to 172.28.1.0/24. "
        f"Routing table:\n{out}"
    )


def test_device2_ip_forwarding_enabled():
    """
    device-2 acts as the router between the two subnets. IP forwarding
    MUST be enabled on it, or multi-hop traffic will silently fail.
    """
    rc, out, err = run_in_container("device-2", "cat /proc/sys/net/ipv4/ip_forward")
    assert rc == 0, f"Failed to read ip_forward setting on device-2: {err}"
    assert out.strip() == "1", (
        f"IP forwarding is disabled on device-2 (value: '{out}'). "
        f"Multi-hop routing between device-1 and device-3 requires this to be enabled."
    )


def test_device2_has_interfaces_on_both_subnets():
    """device-2 must have an interface/IP on each subnet to act as the hop."""
    rc, out, err = run_in_container("device-2", "ip -4 addr show")
    assert rc == 0, f"Failed to read interfaces on device-2: {err}"
    assert "172.28.1.12" in out, f"device-2 missing expected IP on net-a. Output:\n{out}"
    assert "172.28.2.12" in out, f"device-2 missing expected IP on net-b. Output:\n{out}"
