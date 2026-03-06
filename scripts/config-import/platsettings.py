#!/usr/bin/env python3
import argparse
import json
import sys

import requests
import shutup

shutup.please()

# API Endpoint Templates
TOKEN_API_TPL = "{base_url}/api/fmc_platform/v1/auth/generatetoken"
Plat_API_TPL = "{base_url}/api/fmc_config/v1/domain/{domain_uuid}/policy/ftdplatformsettingspolicies"
ATTACH_API_TPL = "{base_url}/api/fmc_config/v1/domain/{domain_uuid}/assignment/policyassignments"

# Global variables to store auth details
headers = {}
domain_uuid = "e276abec-e0f2-11e3-8169-6d9ed49b625f" # Default for cdFMC

def fmc_auth(base_url, is_cdfmc, token, username, password):
    """Authenticates with FMC and sets global headers."""
    global headers, domain_uuid
    if is_cdfmc.lower() == "true":
        headers = {'Authorization': 'Bearer ' + token}
        return

    # On-prem FMC authentication
    try:
        response = requests.post(
            url=TOKEN_API_TPL.format(base_url=base_url),
            auth=(username, password),
            data={},
            verify=False
        )
        response.raise_for_status()
        auth_headers = response.headers
        headers['X-auth-access-token'] = auth_headers['X-auth-access-token']
        domain_uuid = auth_headers["DOMAIN_UUID"]
    except requests.exceptions.RequestException as e:
        print(f"Error: Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)

def get_plat_settings_id(base_url, plat_policy_name):
    """Finds and returns the ID of an Platform policy by its name."""
    api_url = Plat_API_TPL.format(base_url=base_url, domain_uuid=domain_uuid)
    try:
        response = requests.get(url=api_url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        if 'items' not in data:
            print(f"Error: No 'items' key found in Platform policy list response.", file=sys.stderr)
            return None, None

        for policy in data['items']:
            if policy.get('name') == plat_policy_name:
                return policy.get('id'), policy.get('type')

        print(f"Error: Plat Policy with name '{plat_policy_name}' not found.", file=sys.stderr)
        return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to retrieve Plat policies: {e}", file=sys.stderr)
        return None, None

def attach_to_device(base_url, policy_id, policy_type, device_id):
    payload = {
        "type": "PolicyAssignment",
        "policy": {
            "type": policy_type,
            "id": policy_id,
            "name": "vFTD-platform-policy"
        },
        "targets": [
            {
            "id": device_id,
            "type": "Device"
            }]
        }
    api_url = ATTACH_API_TPL.format(base_url=base_url, domain_uuid=domain_uuid)
    try:
        response = requests.post(url=api_url, headers=headers, json=payload, verify=False)
        if response.status_code != 201:
            raise requests.exceptions.RequestException
        
        print("Successfully created policy assignment.")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to attach policy. API responded with: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Fetch FMC Plat Policy ID for Terraform.")
    parser.add_argument('--host', required=True, help="FMC host URL (e.g., https://fmc.example.com)")
    parser.add_argument('--platformpolicy_name', required=True, help="Name of the Plat policy to find.")
    parser.add_argument('--is_cdfmc', help="Flag for cisco Defense Orchestrator (CDO/cdFMC).")
    parser.add_argument('--token', help="API token for cdFMC.")
    parser.add_argument('--user', help="Username for on-prem FMC.")
    parser.add_argument('--password', help="Password for on-prem FMC.")
    parser.add_argument('--deviceid', help="Device to attach to policy")
    args = parser.parse_args()

    # Authenticate
    fmc_auth(args.host, args.is_cdfmc, args.token, args.user, args.password)

    # Get the Policy ID
    policy_id, policy_type = get_plat_settings_id(f"https://{args.host}", args.platformpolicy_name)

    if not policy_id:
        sys.exit(1)


    attach_to_device(f"https://{args.host}", policy_id, policy_type, args.deviceid)
    # IMPORTANT: Print the output as a JSON object to stdout.
    # Terraform's external data source will parse this.
    output = {"platform_policy_id": policy_id}
    print(json.dumps(output))

if __name__ == "__main__":
    main()