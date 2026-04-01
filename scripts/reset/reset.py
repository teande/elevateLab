#!/usr/bin/env python3
"""
cdFMC Lab Reset Script

Cleans the cdFMC/SCC tenant between student lab sessions so the next
deployment runs against a known-good state.

Reset sequence:
  1. Delete S2S VPN topology objects from FMC
  2. Find and deregister old FTD device from CDO (async) + poll until gone
  3. Delete NAT policy (blocks object deletion if left in place)
  4. Delete global network/host objects (re-created by Terraform on next deploy)
  5. Delete the Access Control Policy (re-imported from .sfo on next deploy)
"""

import argparse
import re
import sys
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Matches the hardcoded value used across all other scripts in this project
DOMAIN_UUID = "e276abec-e0f2-11e3-8169-6d9ed49b625f"

POLL_INTERVAL_SEC = 10
POLL_TIMEOUT_SEC = 300

# Must match the names in modules/fmc-vpn/main.tf
VPN_TOPOLOGY_NAMES = {"SecureAccess"}

# Must match var.policies in terraform.tfvars
ACP_NAME = "HQ Firewall Policy"
NAT_POLICY_NAME = "HQ NAT Policy"


def fmc_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def cdo_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── FMC: VPN topology cleanup ─────────────────────────────────────────────────


def list_vpn_topologies(fmc_host, token):
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/policy/ftds2svpns"
    try:
        resp = requests.get(url, headers=fmc_headers(token), verify=False)
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not list VPN topologies: {e}", file=sys.stderr)
        sys.exit(1)


def delete_vpn_topology(fmc_host, token, topology_id, name):
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/policy/ftds2svpns/{topology_id}"
    try:
        resp = requests.delete(url, headers=fmc_headers(token), verify=False)
        if resp.status_code in (200, 204):
            print(f"  Deleted: {name}")
        else:
            print(f"  WARNING: {name} returned {resp.status_code}: {resp.text}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Could not delete {name}: {e}", file=sys.stderr)


def cleanup_vpn_topologies(fmc_host, token):
    print("Step 1: Deleting VPN topology objects...")
    topologies = list_vpn_topologies(fmc_host, token)
    targets = [t for t in topologies if t.get("name") in VPN_TOPOLOGY_NAMES]
    if not targets:
        print("  Nothing to delete — already clean.")
        return
    for t in targets:
        delete_vpn_topology(fmc_host, token, t["id"], t["name"])


# ── CDO: Device deregistration ────────────────────────────────────────────────
#
# CDO API v1 docs: https://developer.cisco.com/docs/cisco-security-cloud-control-firewall-manager/
# API base: https://api.{region}.security.cisco.com/firewall
# Endpoints: GET  /v1/inventory/devices
#            POST /v1/inventory/devices/ftds/cdfmcManaged/{deviceUid}/delete


def derive_cdo_api_base(scc_host):
    """Derive CDO API base URL from SCC portal URL.

    https://us.manage.security.cisco.com → https://api.us.security.cisco.com/firewall
    https://eu.manage.security.cisco.com → https://api.eu.security.cisco.com/firewall
    """
    match = re.match(r"https?://(\w+)\.manage\.security\.cisco\.com", scc_host)
    if match:
        region = match.group(1)
        return f"https://api.{region}.security.cisco.com/firewall"
    # Fallback: assume it's already an API URL
    return scc_host.rstrip("/")


def find_cdo_device(api_base, token, device_name):
    """Return device UID if the named FTD exists in CDO, else None."""
    url = f"{api_base}/v1/inventory/devices"
    try:
        resp = requests.get(
            url, headers=cdo_headers(token), verify=False, params={"limit": "200"}
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        for device in items:
            if device.get("name") == device_name:
                return device.get("uid") or device.get("id")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not query CDO devices: {e}", file=sys.stderr)
        sys.exit(1)


def deregister_cdo_device(api_base, token, device_uid):
    url = f"{api_base}/v1/inventory/devices/ftds/cdfmcManaged/{device_uid}/delete"
    try:
        resp = requests.post(url, headers=cdo_headers(token), verify=False)
        if resp.status_code not in (200, 202, 204):
            print(f"ERROR: Deregistration returned {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Deregistration call failed: {e}", file=sys.stderr)
        sys.exit(1)


def poll_until_gone(api_base, token, device_name):
    """Block until device no longer appears in CDO or timeout."""
    print(f"  Polling every {POLL_INTERVAL_SEC}s (timeout: {POLL_TIMEOUT_SEC}s)...")
    elapsed = 0
    while elapsed < POLL_TIMEOUT_SEC:
        if find_cdo_device(api_base, token, device_name) is None:
            print(f"  Device gone after {elapsed}s.")
            return
        print(f"  Still present at {elapsed}s...")
        time.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC
    print(f"ERROR: Device still present after {POLL_TIMEOUT_SEC}s. Aborting.", file=sys.stderr)
    sys.exit(1)


# ── FMC: NAT policy deletion ──────────────────────────────────────────────────


def delete_nat_policy(fmc_host, token):
    print(f"Step 3: Deleting NAT policy '{NAT_POLICY_NAME}'...")
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/policy/ftdnatpolicies"
    try:
        resp = requests.get(url, headers=fmc_headers(token), verify=False)
        resp.raise_for_status()
        policies = resp.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: Could not list NAT policies: {e}", file=sys.stderr)
        return

    match = next((p for p in policies if p.get("name") == NAT_POLICY_NAME), None)
    if not match:
        print("  NAT policy not found — already clean.")
        return

    del_url = f"{url}/{match['id']}"
    try:
        resp = requests.delete(del_url, headers=fmc_headers(token), verify=False)
        if resp.status_code in (200, 204):
            print(f"  Deleted: {NAT_POLICY_NAME}")
        else:
            print(f"  WARNING: NAT delete returned {resp.status_code}: {resp.text}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: Could not delete NAT policy: {e}", file=sys.stderr)


# ── FMC: Global object cleanup ────────────────────────────────────────────────
#
# These objects are created by Terraform but persist on the cdFMC tenant after
# a reset (state is wiped with the pod but the tenant is reused across events).
# Delete them here so the next deploy can re-create them cleanly.

# fmc-networking: network and host objects
_NETWORK_OBJECTS = {
    "Branch-EVPN-Overlay-Main",
    "Branch-EVPN-Underlay",
    "Branch-EVPN-Overlay-PROD",
    "Branch-EVPN-Overlay-IOT",
}
_HOST_OBJECTS = {
    "ExtGW",
    "En-Cat8Kv",
    "BRANCH-SITE-105-ROUTER",
    "HQ-SITE10-CEDGE8Kv",
    "Secure_Access_BGP_Peer_1",
    "Secure_Access_BGP_Peer_2",
}
# fmc-network-objects: OSPF-specific network objects
_OSPF_NETWORK_OBJECTS = {
    "Apps",
    "Attacker",
    "Data-Center",
    "DMZ",
    "Outside",
    "Transport",
}


def _list_fmc_objects(fmc_host, token, object_type):
    """Return list of FMC objects of the given type (networks, hosts, etc.)."""
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/object/{object_type}"
    try:
        resp = requests.get(
            url, headers=fmc_headers(token), verify=False, params={"limit": 200}
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: Could not list {object_type}: {e}", file=sys.stderr)
        return []


def _delete_fmc_object(fmc_host, token, object_type, obj_id, name):
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/object/{object_type}/{obj_id}"
    try:
        resp = requests.delete(url, headers=fmc_headers(token), verify=False)
        if resp.status_code in (200, 204):
            print(f"  Deleted: {name}")
        else:
            print(f"  WARNING: {name} returned {resp.status_code}: {resp.text}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: Could not delete {name}: {e}", file=sys.stderr)


def _cleanup_objects_by_name(fmc_host, token, object_type, target_names):
    items = _list_fmc_objects(fmc_host, token, object_type)
    matches = [i for i in items if i.get("name") in target_names]
    if not matches:
        print(f"  No {object_type} to delete — already clean.")
        return
    for obj in matches:
        _delete_fmc_object(fmc_host, token, object_type, obj["id"], obj["name"])


def cleanup_global_objects(fmc_host, token):
    print("Step 4: Deleting global FMC network/host objects...")
    _cleanup_objects_by_name(fmc_host, token, "networks", _NETWORK_OBJECTS | _OSPF_NETWORK_OBJECTS)
    _cleanup_objects_by_name(fmc_host, token, "hosts", _HOST_OBJECTS)


# ── FMC: ACP deletion ─────────────────────────────────────────────────────────


def get_acp_id(fmc_host, token):
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/policy/accesspolicies"
    try:
        resp = requests.get(url, headers=fmc_headers(token), verify=False)
        resp.raise_for_status()
        for policy in resp.json().get("items", []):
            if policy.get("name") == ACP_NAME:
                return policy["id"]
        print(f"  WARNING: ACP '{ACP_NAME}' not found.", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not list ACPs: {e}", file=sys.stderr)
        sys.exit(1)


def delete_acp(fmc_host, token):
    print(f"Step 5: Deleting Access Control Policy '{ACP_NAME}'...")
    acp_id = get_acp_id(fmc_host, token)
    if not acp_id:
        print("  ACP not found — already clean.")
        return
    url = f"https://{fmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/policy/accesspolicies/{acp_id}"
    try:
        resp = requests.delete(url, headers=fmc_headers(token), verify=False)
        if resp.status_code in (200, 204):
            print(f"  Deleted: {ACP_NAME}")
        else:
            print(f"  WARNING: ACP delete returned {resp.status_code}: {resp.text}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Could not delete ACP: {e}", file=sys.stderr)


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Reset cdFMC/SCC tenant between student lab sessions."
    )
    parser.add_argument("--scc-host", required=True, help="SCC base URL (e.g. https://us.manage.security.cisco.com)")
    parser.add_argument("--fmc-host", required=True, help="cdFMC hostname (no https://)")
    parser.add_argument("--token",    required=True, help="SCC/CDO API token")
    parser.add_argument("--device-name", required=True, help="FTD device name to deregister")
    args = parser.parse_args()

    print("=" * 54)
    print("  cdFMC Lab Reset")
    print("=" * 54)

    # Step 1 — VPN topologies
    cleanup_vpn_topologies(args.fmc_host, args.token)

    # Step 2 — CDO device deregistration
    api_base = derive_cdo_api_base(args.scc_host)
    print(f"Step 2: Looking for '{args.device_name}' in CDO ({api_base})...")
    uid = find_cdo_device(api_base, args.token, args.device_name)
    if uid:
        print(f"  Found (UID: {uid}). Initiating deregistration...")
        deregister_cdo_device(api_base, args.token, uid)
        print("  Waiting for deregistration to complete...")
        poll_until_gone(api_base, args.token, args.device_name)
    else:
        print(f"  '{args.device_name}' not found in CDO — already deregistered.")

    # Step 3 — Delete NAT policy (blocks object deletion if left in place)
    delete_nat_policy(args.fmc_host, args.token)

    # Step 4 — Delete global network/host objects (re-created by Terraform on next deploy)
    cleanup_global_objects(args.fmc_host, args.token)

    # Step 5 — Delete ACP (re-imported from .sfo on next deploy)
    delete_acp(args.fmc_host, args.token)

    print("=" * 54)
    print("  Reset complete. Ready for next deployment.")
    print("=" * 54)


if __name__ == "__main__":
    main()
