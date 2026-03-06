#!/usr/bin/env python3
"""
cdFMC REST API OSPF Automation Configuration

This configuration can be overridden by environment variables or command line arguments
"""

import os
import sys

# cdFMC Connection Settings - can be overridden by environment variables or arguments
FMC_URL = os.getenv('FMC_URL', "")  # Your cdFMC URL
API_KEY = os.getenv('API_KEY', "")

# Static domain UUID for cdFMC (this is constant)
DOMAIN_UUID = "e276abec-e0f2-11e3-8169-6d9ed49b625f"

# Runtime parameters (will be set by Terraform)
DEVICE_ID = None  # Will be provided by Terraform
NETWORK_IDS = {}  # Network object IDs from Terraform

# Function to update configuration from Terraform
def update_config_from_terraform(fmc_url=None, api_key=None, device_id=None, network_ids=None):
    """Update configuration values from Terraform parameters"""
    global FMC_URL, API_KEY, DEVICE_ID, NETWORK_IDS
    
    if fmc_url:
        FMC_URL = fmc_url if fmc_url.startswith('https://') else f"https://{fmc_url}"
        if not FMC_URL.endswith('/'):
            FMC_URL += '/'
    
    if api_key:
        API_KEY = api_key
        
    if device_id:
        DEVICE_ID = device_id
        
    if network_ids:
        NETWORK_IDS = network_ids

# Device and OSPF Settings (static configuration)
DEVICE_NAME = "HQ_FTDv"  # Device name (note underscore, not space)
OSPF_PROCESS_ID = "1"
OSPF_ROUTER_ID = "1.1.1.1"
OSPF_AREA_ID = "0"

# Networks to add to OSPF Area (from your screenshot)
OSPF_NETWORKS = [
    "Attacker",
    "Data-Center", 
    "Apps",
    "DMZ",
    "Outside",
    "Transport"
]
