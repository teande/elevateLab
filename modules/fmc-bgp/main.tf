terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

################################################################################################
# BGP Configuration Module
# Configures BGP on the FTD device via Python REST API (provider does not support BGP natively)
# Runs after OSPF, before VPN
################################################################################################

# Requires shared venv at scripts/.venv (created by deploy_prep_pod_configuration.sh)
resource "null_resource" "configure_bgp" {
  provisioner "local-exec" {
    command     = "../.venv/bin/python3 bgp_routing.py --fmc-url '${var.cdfmc_host}' --api-key '${var.scc_token}' --device-id '${var.devices[0].id}' --network-ids '${jsonencode(var.network_ids)}'"
    working_dir = "${path.root}/scripts/bgp"
    interpreter = ["/bin/bash", "-c"]
  }

  triggers = {
    fmc_url     = var.cdfmc_host
    api_key     = md5(var.scc_token)
    device_id   = var.devices[0].id
    network_ids = jsonencode(var.network_ids)
  }
}
