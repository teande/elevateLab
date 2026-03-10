#! .venv/bin/env python3

import argparse
import json
import sys
from pathlib import Path

import requests
import shutup

shutup.please()

# --- Configuration ---
# These can be overridden by command-line arguments
CDFMC_BASE_URL = ""
API_TOKEN = ""
BACKUP_FILE = "automation.sfo"  # Default backup file name
IS_CDFMC = True  # Set to False for on-prem FMC

# --- API Definitions ---
# Note: These will be formatted later
TOKEN_API_TPL = "{base_url}/api/fmc_platform/v1/auth/generatetoken"
IMPORT_API_TPL = (
    "{base_url}/api/fmc_config/v1/domain/{domainUUID}/devices/operational/imports"
)

# --- Global Variables ---
domainUUID = "e276abec-e0f2-11e3-8169-6d9ed49b625f"  # Default for cdFMC
headers = {}


def fmc_auth(base_url, is_cdfmc, token, username, password):
    global headers, domainUUID
    if is_cdfmc:
        headers = {"Authorization": "Bearer " + token}
        return

    # On-prem FMC authentication
    token_api = TOKEN_API_TPL.format(base_url=base_url)
    response = requests.post(
        url=token_api, auth=(username, password), data={}, verify=False
    )
    response.raise_for_status()  # Will raise an exception for non-2xx status codes

    auth_headers = response.headers
    headers["X-auth-access-token"] = auth_headers["X-auth-access-token"]
    domainUUID = auth_headers["DOMAIN_UUID"]
    print("Successfully authenticated with on-prem FMC.")


def main(args):
    base_url = args.host if args.host else CDFMC_BASE_URL
    token = args.token if args.token else API_TOKEN
    backup_file = args.backup_file if args.backup_file else BACKUP_FILE

    try:
        fmc_auth(base_url, IS_CDFMC, token, args.user, args.password)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    import_url = IMPORT_API_TPL.format(base_url=base_url, domainUUID=domainUUID)
    backup_file_path = Path(__file__).parent / backup_file

    if not backup_file_path.is_file():
        print(f"Error: Backup file not found at '{backup_file_path}'")
        sys.exit(1)

    import_options = {"includeSharedPolicies": True, "conflictOption": "LATEST"}
    # Define payload data programmatically
    if "s2s" in backup_file:
        import_options = {"includeS2sVpnPoliciesOnly": True, "conflictOption": "LATEST"}

    device_list = ["cf76391c-1087-11ee-a9af-e1a3028a9c82"]

    print(f"Attempting to import '{backup_file_path.name}' to '{import_url}'...")

    try:
        with open(backup_file_path, "rb") as f:
            # Combine all fields into a single dictionary for the 'files' parameter
            multipart_payload = {
                "deviceList": (None, json.dumps(device_list)),
                "importOptions": (None, json.dumps(import_options)),
                "payloadFile": (backup_file_path.name, f, "application/octet-stream"),
                "name": "Automation_Backup",
            }

            # The 'requests' library sets the 'Content-Type' with boundary automatically
            response = requests.post(
                import_url, headers=headers, files=multipart_payload, verify=False
            )

            # Check for HTTP errors
            # response.raise_for_status()

            print(f"Status Code: {response.status_code}")
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))

    except (
        requests.exceptions.RequestException,
        ConnectionError,
        OSError,
        Exception,
    ) as e:
        print(f"An error occurred during the request: {e}")
        # Only try to access response if this is a requests exception
        if (
            isinstance(e, requests.exceptions.RequestException)
            and hasattr(e, "response")
            and e.response is not None
        ):
            print(f"Response Body: {e.response.text}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import device configuration to Cisco FMC or cdFMC."
    )
    parser.add_argument(
        "--host",
        help="Address of Cisco FMC/cdFMC. Defaults to pre-configured cdFMC URL.",
    )
    parser.add_argument(
        "--token", help="Bearer Token for cdFMC. Defaults to pre-configured token."
    )
    parser.add_argument(
        "--backup-file", help="Backup SFO file to pass configuration with."
    )
    parser.add_argument("--user", help="Username for on-prem FMC.")
    parser.add_argument("--password", help="Password for on-prem FMC.")
    args = parser.parse_args()
    main(args)


# {
#   "deviceList": [
#     "cf76391c-1087-11ee-a9af-e1a3028a9c82"
#   ],
#   "exportOptions": {
#       "includeSharedPolicies": "true",
#       "conflictOption": "NEW"
#   }
# }
