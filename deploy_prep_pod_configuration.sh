#!/bin/bash

################################################################################################
# Pod Preparation Script for Event
# This script handles the complete preparation of a FMC lab pod including:
# - Device registration and onboarding
# - VTI interface discovery and import (for existing interfaces)
# - Security zone attachment to interfaces
# - Network configuration and policies
# - VPN site-to-site configuration
################################################################################################

set -e  # Exit on any error

echo "======================================"
echo "Pod Preparation Process Starting"
echo "======================================"

# Create progress tracking file
PROGRESS_FILE=".pod_prepare_progress"

# Extract FMC credentials from terraform.tfvars for API calls
if [ ! -f terraform.tfvars ]; then
    echo "ERROR: terraform.tfvars not found. Copy terraform.tfvars.ignore and populate credentials."
    exit 1
fi
CDFMC_HOST=$(grep -E '^\s*cdfmc_host' terraform.tfvars | sed 's/.*=\s*"\(.*\)"/\1/' | tr -d '/')
SCC_TOKEN=$(grep -E '^\s*scc_token' terraform.tfvars | sed 's/.*=\s*"\(.*\)"/\1/')
DOMAIN_UUID="e276abec-e0f2-11e3-8169-6d9ed49b625f"

# Function to check if step was completed
check_step_completed() {
    local step_name=$1
    if [ -f "$PROGRESS_FILE" ] && grep -q "^$step_name$" "$PROGRESS_FILE"; then
        return 0  # Step completed
    else
        return 1  # Step not completed
    fi
}

# Function to mark step as completed
mark_step_completed() {
    local step_name=$1
    echo "$step_name" >> "$PROGRESS_FILE"
    echo "✅ Step $step_name completed and cached"
}

# Function to check if resource exists in terraform state (fast check)
resource_exists_in_state() {
    local resource_name=$1
    terraform state list | grep -q "^$resource_name$" 2>/dev/null
}

# Step 1: Register the device first
if check_step_completed "device_registration"; then
    echo "Step 1: Device registration already completed (cached) ⚡"
else
    echo "Step 1: Registering FTD device..."
    terraform apply -target=module.fmc_devices -auto-approve
    mark_step_completed "device_registration"
fi

# Step 2: Discover VTI interfaces using data-only module
if check_step_completed "vti_discovery"; then
    echo "Step 2: VTI discovery already completed (cached) ⚡"
else
    echo "Step 2: Discovering existing VTI interfaces..."
    terraform apply -target=module.fmc_vti_discovery -auto-approve
    mark_step_completed "vti_discovery"
fi

# Step 3: Extract IDs (only if needed)
if check_step_completed "id_extraction"; then
    echo "Step 3: ID extraction already completed (cached) ⚡"
    # Load cached IDs
    source .vti_ids_cache 2>/dev/null || {
        echo "Cache corrupted, re-extracting IDs..."
        rm -f .vti_ids_cache
    }
else
    echo "Step 3: Extracting device, VTI interface, and NetFlowGrp IDs..."

    # Refresh outputs only once
    terraform refresh -target=module.fmc_devices -target=module.fmc_vti_discovery

    # Get device ID
    DEVICE_ID=$(terraform state show 'module.fmc_devices.data.fmc_device.devices[0]' | grep -E '^\s*id\s*=' | cut -d'"' -f2 2>/dev/null || echo "")

    if [ -z "$DEVICE_ID" ] || [ "$DEVICE_ID" = "null" ]; then
        echo "ERROR: Could not get device ID. Device may not be registered yet."
        exit 1
    fi

    # Get VTI interface IDs using faster state show commands
    VTI1_ID=$(terraform state show 'module.fmc_vti_discovery.data.fmc_device_vti_interface.WAN_static_vti_1' | grep -E '^\s*id\s*=' | cut -d'"' -f2 2>/dev/null || echo "")
    VTI2_ID=$(terraform state show 'module.fmc_vti_discovery.data.fmc_device_vti_interface.WAN_static_vti_2' | grep -E '^\s*id\s*=' | cut -d'"' -f2 2>/dev/null || echo "")

    # Get NetFlowGrp ID via FMC API (may not exist on fresh tenants — created in Step 6 if absent)
    NETFLOW_ID=$(curl -s -k \
        -H "Authorization: Bearer $SCC_TOKEN" \
        -H "Content-Type: application/json" \
        "https://$CDFMC_HOST/api/fmc_config/v1/domain/$DOMAIN_UUID/object/interfacegroups?limit=100" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); grp=[i for i in d.get('items',[]) if i.get('name')=='NetFlowGrp']; print(grp[0]['id'] if grp else '')" 2>/dev/null || echo "")

    # Cache the IDs for future runs
    cat > .vti_ids_cache << EOF
DEVICE_ID="$DEVICE_ID"
VTI1_ID="$VTI1_ID"
VTI2_ID="$VTI2_ID"
NETFLOW_ID="$NETFLOW_ID"
EOF

    mark_step_completed "id_extraction"
fi

echo "Device ID: $DEVICE_ID"
echo "VTI1 ID (Tunnel1): $VTI1_ID"
echo "VTI2 ID (Tunnel2): $VTI2_ID"
echo "NetFlow Group ID: $NETFLOW_ID"

# Validate critical IDs before attempting imports
if [ -z "$VTI1_ID" ] || [ -z "$VTI2_ID" ]; then
    echo "ERROR: VTI IDs could not be determined. Delete .pod_prepare_progress and .vti_ids_cache and re-run."
    exit 1
fi

# Step 4: Import VTI interfaces into state (always runs — resource_exists_in_state handles idempotency)
echo "Step 4: Importing VTI interfaces into Terraform state..."

import_vti() {
    local resource_name=$1
    local vti_id=$2
    local description=$3

    # Fast check: if resource already exists in state, skip
    if resource_exists_in_state "$resource_name"; then
        echo "⚡ $description already in state (skipping)"
        return 0
    fi

    echo "Importing $description..."
    if terraform import "$resource_name" "$DEVICE_ID,$vti_id"; then
        echo "✅ Successfully imported $description"
    else
        echo "ERROR: ❌ Import failed for $description (DEVICE_ID=$DEVICE_ID, VTI_ID=$vti_id)"
        echo "       Ensure the device is registered and VTI interfaces exist on the FTD."
        exit 1
    fi
}

import_vti "module.fmc_interfaces.fmc_device_vti_interface.WAN_static_vti_1" "$VTI1_ID" "WAN Static VTI 1 (Tunnel1)"
import_vti "module.fmc_interfaces.fmc_device_vti_interface.WAN_static_vti_2" "$VTI2_ID" "WAN Static VTI 2 (Tunnel2)"

# Step 5: Import NetFlowGrp interface group (with smart checking)
if check_step_completed "netflow_import"; then
    echo "Step 5: NetFlowGrp import already completed (cached) ⚡"
else
    echo "Step 5: Importing NetFlowGrp interface group into Terraform state..."

    # Check if NetFlowGrp resource already exists in state
    if resource_exists_in_state "module.fmc_interface_groups.fmc_interface_group.netflow_managed"; then
        echo "⚡ NetFlowGrp already in state (skipping)"
    else
        if [ -n "$NETFLOW_ID" ] && [ "$NETFLOW_ID" != "null" ]; then
            echo "Importing NetFlowGrp interface group..."
            if terraform import "module.fmc_interface_groups.fmc_interface_group.netflow_managed" "$NETFLOW_ID"; then
                echo "✅ Successfully imported NetFlowGrp interface group"
            else
                echo "⚠️  Import failed for NetFlowGrp (may already be imported)"
            fi
        else
            echo "❌ Skipping NetFlowGrp import - ID not found"
        fi
    fi

    mark_step_completed "netflow_import"
fi

# Step 6: Apply the core configuration excluding VPN module (with smart checking)
if check_step_completed "core_config"; then
    echo "Step 6: Core configuration already applied (cached) ⚡"
else
    echo "Step 6: Applying core configuration (interfaces, networking, network objects, and policies)..."
    # Apply interfaces, networking, network objects, and policies - VTI interfaces are already imported
    terraform apply -target=module.fmc_interfaces \
                    -target=module.fmc_networking \
                    -target=module.fmc_network_objects \
                    -target=module.fmc_interface_groups \
                    -target=module.fmc_policies \
                    -auto-approve -refresh=false
    mark_step_completed "core_config"
fi

# Step 7a: Apply OSPF configuration (before BGP and VPN)
echo "Step 7: Applying OSPF configuration..."
terraform apply -target=module.fmc_ospf -auto-approve -refresh=false

# Step 7b: Apply BGP configuration (after OSPF, before VPN)
echo "Step 7b: Applying BGP configuration..."
terraform apply -target=module.fmc_bgp -auto-approve -refresh=false

# Step 8: Apply VPN configuration as final step (always last)
echo "Step 8: Applying VPN configuration as final step..."
terraform apply -target=module.fmc_vpn -auto-approve -refresh=false

# Clean up cache files on successful completion
rm -f "$PROGRESS_FILE" .vti_ids_cache

echo "======================================"
echo "Pod Preparation Process Complete!"
echo "======================================"
echo ""
echo "Summary:"
echo "✅ Device registered"
echo "✅ VTI interfaces discovered"
echo "✅ VTI interfaces imported into state"
echo "✅ NetFlowGrp interface group imported and managed"
echo "✅ Security zones attached to VTI interfaces"
echo "✅ Networking and network objects configured"
echo "✅ Policies configured"
echo "✅ OSPF configuration applied"
echo "✅ BGP configuration applied"
echo "✅ VPN configuration applied (final step)"
echo "✅ Full infrastructure deployed"
echo ""
echo "💡 Tip: Cache files cleaned up. Re-run script anytime for incremental updates!"
