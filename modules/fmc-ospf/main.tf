terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

################################################################################################
# OSPF Configuration Module
# This module configures OSPF on FTD devices using the existing Python script
################################################################################################

# Execute OSPF configuration using the script in the scripts directory
# Requires shared venv at scripts/.venv (created by deploy_prep_pod_configuration.sh)
resource "null_resource" "configure_ospf" {
  provisioner "local-exec" {
    command     = "../.venv/bin/python3 cdfmc_ospf_automation.py --fmc-url '${var.cdfmc_host}' --api-key '${var.scc_token}' --device-id '${var.devices[0].id}' --network-ids '${jsonencode(var.network_ids)}'"
    working_dir = "${path.root}/scripts/ospf"
    interpreter = ["/bin/bash", "-c"]
  }

  # Run when configuration changes
  triggers = {
    fmc_url     = var.cdfmc_host
    api_key     = md5(var.scc_token)
    device_id   = var.devices[0].id
    network_ids = jsonencode(var.network_ids)
  }
}
