"""
Connectivity tests for the lab topology.

Topology reminder:
    device-1 (172.28.1.11) --- device-2 (172.28.1.12 / 172.28.2.12) --- device-3 (172.28.2.13)

device-1 and device-3 are on different subnets and can only reach each other
THROUGH device-2 acting as a router. This validates both direct links and the
multi-hop path.
"""

from conftest import ping

DEVICE_1_IP = "172.28.1.11"
DEVICE_2_NET_A_IP = "172.28.1.12"
DEVICE_2_NET_B_IP = "172.28.2.12"
DEVICE_3_IP = "172.28.2.13"


def test_device1_can_reach_device2():
    """Direct link: device-1 -> device-2 on net-a."""
    reachable, out, err = ping("device-1", DEVICE_2_NET_A_IP)
    assert reachable, f"device-1 could not reach device-2 ({DEVICE_2_NET_A_IP}). stderr: {err}"


def test_device2_can_reach_device3():
    """Direct link: device-2 -> device-3 on net-b."""
    reachable, out, err = ping("device-2", DEVICE_3_IP)
    assert reachable, f"device-2 could not reach device-3 ({DEVICE_3_IP}). stderr: {err}"


def test_device1_can_reach_device3_multihop():
    """
    Multi-hop: device-1 -> device-3, routed through device-2.
    This only works if device-2 has IP forwarding enabled and both
    endpoints have the correct static route configured.
    """
    reachable, out, err = ping("device-1", DEVICE_3_IP)
    assert reachable, (
        f"device-1 could not reach device-3 ({DEVICE_3_IP}) via multi-hop route "
        f"through device-2. stderr: {err}"
    )


def test_device3_can_reach_device1_multihop():
    """Multi-hop reachability should work symmetrically in the reverse direction."""
    reachable, out, err = ping("device-3", DEVICE_1_IP)
    assert reachable, (
        f"device-3 could not reach device-1 ({DEVICE_1_IP}) via multi-hop route "
        f"through device-2. stderr: {err}"
    )


def test_route_removal_breaks_connectivity():
    """
    Negative test: if device-1's route to device-3's subnet is removed,
    connectivity should correctly FAIL (proving our tests can actually
    detect a broken network, not just confirm a working one).

    The route is restored afterward so later tests aren't affected.
    """
    from conftest import run_in_container

    # Remove the route
    run_in_container("device-1", "ip route del 172.28.2.0/24")

    reachable, out, err = ping("device-1", DEVICE_3_IP, timeout=5)

    # Restore the route regardless of test outcome
    run_in_container("device-1", "ip route add 172.28.2.0/24 via 172.28.1.12")

    assert not reachable, (
        "device-1 could still reach device-3 after its route was removed -- "
        "the test failed to detect a broken network path."
    )
