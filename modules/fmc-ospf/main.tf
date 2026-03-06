terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

################################################################################################
# OSPF Configuration Module
# This module configures OSPF on FTD devices using the existing Python script
################################################################################################

# Create Python virtual environment and install requirements
resource "null_resource" "install_requirements_for_ospf" {
  provisioner "local-exec" {
    working_dir = "${path.root}/scripts/ospf"
    command     = "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    interpreter = ["/bin/bash", "-c"]
  }
}

# Execute OSPF configuration using the script in the scripts directory
resource "null_resource" "configure_ospf" {
  depends_on = [null_resource.install_requirements_for_ospf]

  provisioner "local-exec" {
    command     = ".venv/bin/python3 cdfmc_ospf_automation.py --fmc-url '${var.cdfmc_host}' --api-key '${var.scc_token}' --device-id '${var.devices[0].id}' --network-ids '${jsonencode(var.network_ids)}'"
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
