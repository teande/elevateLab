#!/usr/bin/env python3
"""
cdFMC BGP Routing Configurator

Integrated with Terraform — credentials and device ID passed via CLI arguments.
Run standalone for testing by passing all required flags explicitly.
"""

import argparse
import json

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Fixed constants for this lab environment ──────────────────────────────────
DOMAIN_UUID = "e276abec-e0f2-11e3-8169-6d9ed49b625f"
AS_NUMBER = "65532"
NEIGHBORS = [
    {"address": "169.254.0.5", "remoteAs": "64512"},
    {"address": "169.254.0.9", "remoteAs": "64512"},
]
ADVERTISED_NETWORKS = ["Data-Center"]

# ── Runtime values — set in main() from CLI args ──────────────────────────────
BASE_URL = None
HEADERS = None


def parse_args():
    parser = argparse.ArgumentParser(description="cdFMC BGP Routing Configurator")
    parser.add_argument("--fmc-url", required=True, help="cdFMC hostname (no https://)")
    parser.add_argument("--api-key", required=True, help="Bearer token")
    parser.add_argument("--device-id", required=True, help="FTD device UUID")
    parser.add_argument(
        "--network-ids",
        required=True,
        help='JSON map of network name to UUID, e.g. \'{"Data-Center":"uuid"}\'',
    )
    return parser.parse_args()


def get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, verify=False)
    r.raise_for_status()
    return r.json()


def post(url, payload):
    r = requests.post(url, headers=HEADERS, json=payload, verify=False)
    if not r.ok:
        print(f"  ERROR {r.status_code}: {r.text}")
        r.raise_for_status()
    return r.json()


def put(url, payload):
    r = requests.put(url, headers=HEADERS, json=payload, verify=False)
    if not r.ok:
        print(f"  ERROR {r.status_code}: {r.text}")
        r.raise_for_status()
    return r.json()


# ── Step 1: BGP General Settings ─────────────────────────────────────────────


def ensure_bgp_general_settings(device_id):
    """
    bgpgeneralsettings must exist before /routing/bgp can be used.
    Creates it if absent, skips if already present.
    """
    gs_url = (
        f"{BASE_URL}/domain/{DOMAIN_UUID}/devices/devicerecords"
        f"/{device_id}/routing/bgpgeneralsettings"
    )

    try:
        data = get(gs_url, params={"limit": 10})
        items = data.get("items", [])
        if items:
            existing_id = items[0]["id"]
            print(
                f"    BGP general settings already exist (ID: {existing_id}) — skipping."
            )
            return existing_id
    except Exception:
        pass

    print("    No BGP general settings found — creating...")
    payload = {
        "type": "BGPGeneralSettings",
        "name": "AsaBGPGeneralTable",
        "asNumber": AS_NUMBER,
        "routerId": "AUTOMATIC",
        "bgptimers": {
            "type": "bgptimers",
            "keepAlive": 60,
            "holdTime": 180,
            "minHoldTime": 0,
        },
        "bestPath": {
            "type": "bgpbestpath",
            "defaultLocalPreferenceValue": 100,
            "alwaysCompareMed": False,
            "bestPathCompareRouterId": False,
            "deterministicMed": False,
            "bestPathMedMissingAsWorst": False,
        },
        "bgpGracefulRestart": {
            "type": "bgpgracefulrestart",
            "gracefulRestart": False,
            "gracefulRestartRestartTime": 120,
            "gracefulRestartStalePathTime": 360,
        },
        "aggregateTimer": 30,
        "scanTime": 60,
        "maxasLimit": 0,
        "fastExternalFallOver": True,
        "enforceFirstAs": True,
        "asnotationDot": False,
        "bgpNextHopTriggerDelay": 5,
        "bgpNextHopTriggerEnable": True,
        "logNeighborChanges": True,
        "transportPathMtuDiscovery": True,
    }

    result = post(gs_url, payload)
    gs_id = result.get("id")
    print(f"    Created BGP general settings (ID: {gs_id})")
    return gs_id


# ── Step 2: BGP Address Family (neighbors + networks) ────────────────────────


def get_existing_bgp(device_id):
    url = (
        f"{BASE_URL}/domain/{DOMAIN_UUID}/devices/devicerecords/{device_id}/routing/bgp"
    )
    try:
        data = get(url, params={"limit": 10})
        items = data.get("items", [])
        if items:
            bgp_id = items[0]["id"]
            full = get(f"{url}/{bgp_id}")
            return bgp_id, full
    except Exception:
        pass
    return None, None


def build_bgp_payload(obj_map, bgp_id=None):
    neighbor_list = []
    for nbr in NEIGHBORS:
        neighbor_list.append(
            {
                "type": "neighboripv4",
                "ipv4Address": nbr["address"],
                "remoteAs": nbr["remoteAs"],
                "neighborGeneral": {
                    "type": "neighborgeneral",
                    "enableAddress": True,
                    "shutdown": False,
                    "fallOverBFD": "NONE",
                    "asOverride": False,
                },
                "neighborAdvanced": {
                    "type": "neighboradvanced",
                    "neighborHops": {
                        "type": "neighborebgpmultihop",
                        "maxHopCount": 1,
                        "disableConnectedCheck": False,
                    },
                    "neighborVersion": 0,
                    "nextHopSelf": False,
                    "neighborWeight": 0,
                    "sendCommunity": False,
                    "neighborTransportConnectionMode": {
                        "type": "neighbortransportconnectionmode",
                        "establishTCPSession": False,
                    },
                    "neighborTransportPathMTUDiscovery": {
                        "type": "neighbortransportpathmtudiscovery",
                        "disable": True,
                    },
                },
                "neighborTimers": {
                    "type": "neighbortimers",
                    "keepAliveInterval": 60,
                    "holdTime": 180,
                    "minimumHoldTime": 0,
                },
                "neighborRoutes": {"removePrivateAs": False},
                "neighborFiltering": {},
            }
        )

    network_list = []
    for name in ADVERTISED_NETWORKS:
        if name not in obj_map:
            raise ValueError(f"Network object '{name}' not found in --network-ids!")
        o = obj_map[name]
        network_list.append(
            {
                "ipv4Address": {
                    "type": o["type"],
                    "id": o["id"],
                    "name": name,
                }
            }
        )

    payload = {
        "type": "bgp",
        "name": "bgp",
        "asNumber": AS_NUMBER,
        "addressFamilyIPv4": {
            "type": "afipv4",
            "neighbors": neighbor_list,
            "networks": network_list,
            "autoSummary": False,
            "bgpSupressInactive": False,
            "synchronization": False,
            "bgpRedistributeInternal": False,
            "defaultInformationOrginate": False,
        },
    }

    if bgp_id:
        payload["id"] = bgp_id

    return payload


def main():
    global BASE_URL, HEADERS

    args = parse_args()

    BASE_URL = f"https://{args.fmc_url}/api/fmc_config/v1"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {args.api_key}",
    }

    # Build obj_map from passed --network-ids JSON (name → UUID).
    # Advertised networks are always Network objects in this lab.
    raw_ids = json.loads(args.network_ids)
    obj_map = {name: {"id": id_, "type": "Network"} for name, id_ in raw_ids.items()}

    print("=" * 60)
    print("cdFMC BGP Routing Configurator")
    print("=" * 60)
    print(f"\n  Device ID  : {args.device_id}")
    print(f"  AS Number  : {AS_NUMBER}")
    print(f"  Neighbors  : {[n['address'] for n in NEIGHBORS]}")
    print(f"  Networks   : {ADVERTISED_NETWORKS}")

    print("\n[1] Ensuring BGP general settings exist...")
    ensure_bgp_general_settings(args.device_id)

    print("\n[2] Checking for existing BGP address family config...")
    bgp_url = (
        f"{BASE_URL}/domain/{DOMAIN_UUID}/devices/devicerecords"
        f"/{args.device_id}/routing/bgp"
    )
    bgp_id, _ = get_existing_bgp(args.device_id)
    payload = build_bgp_payload(obj_map, bgp_id=bgp_id)

    print("\n[3] Pushing BGP configuration...")
    if bgp_id:
        print(f"    Existing BGP found (ID: {bgp_id}) — updating via PUT...")
        result = put(f"{bgp_url}/{bgp_id}", payload)
    else:
        print("    No existing BGP — creating via POST...")
        result = post(bgp_url, payload)

    print(f"    OK — BGP ID    : {result.get('id', 'n/a')}")
    print(f"         AS Number : {result.get('asNumber')}")
    af = result.get("addressFamilyIPv4", {})
    nbrs = [n.get("ipv4Address") for n in af.get("neighbors", [])]
    nets = [n.get("ipv4Address", {}).get("name") for n in af.get("networks", [])]
    print(f"         Neighbors : {nbrs}")
    print(f"         Networks  : {nets}")

    print("\n" + "=" * 60)
    print("Done. Remember to DEPLOY the policy to the device in FMC!")
    print("=" * 60)


if __name__ == "__main__":
    main()
