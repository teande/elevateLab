#!/bin/bash

################################################################################
# Lab Reset Script
# Cleans the cdFMC/SCC tenant between student sessions so the deploy script
# runs against a known-good state.
#
# Usage: ./reset.sh
# Reads scc_token, scc_host, cdfmc_host, and device_name from terraform.tfvars
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESET_DIR="$SCRIPT_DIR/scripts/reset"
TFVARS="$SCRIPT_DIR/terraform.tfvars"

if [ ! -f "$TFVARS" ]; then
    echo "ERROR: terraform.tfvars not found. Copy terraform.tfvars.ignore and fill in values."
    exit 1
fi

# Parse terraform.tfvars — handles:  key = "value"  and  key = ["value"]
parse_tfvar() {
    local key=$1
    grep -E "^${key}\s*=" "$TFVARS" | sed 's/.*=\s*//' | tr -d ' \t[]' | tr ',' '\n' | tr -d '"' | head -1
}

SCC_TOKEN=$(parse_tfvar "scc_token")
SCC_HOST=$(parse_tfvar "scc_host")
CDFMC_HOST=$(parse_tfvar "cdfmc_host")
DEVICE_NAME=$(parse_tfvar "device_name")

if [ -z "$SCC_TOKEN" ] || [ -z "$SCC_HOST" ] || [ -z "$CDFMC_HOST" ] || [ -z "$DEVICE_NAME" ]; then
    echo "ERROR: One or more required values missing from terraform.tfvars."
    echo "  scc_token:   ${SCC_TOKEN:-(missing)}"
    echo "  scc_host:    ${SCC_HOST:-(missing)}"
    echo "  cdfmc_host:  ${CDFMC_HOST:-(missing)}"
    echo "  device_name: ${DEVICE_NAME:-(missing)}"
    exit 1
fi

# Set up shared Python venv (same one used by deploy script)
VENV_DIR="$SCRIPT_DIR/scripts/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating shared Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/scripts/requirements.txt"
fi

# Run reset
cd "$RESET_DIR"
"$VENV_DIR/bin/python3" reset.py \
    --scc-host   "$SCC_HOST"   \
    --fmc-host   "$CDFMC_HOST" \
    --token      "$SCC_TOKEN"  \
    --device-name "$DEVICE_NAME"
