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

resource "null_resource" "install_requirements_for_bgp" {
  provisioner "local-exec" {
    working_dir = "${path.root}/scripts/bgp"
    command     = "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    interpreter = ["/bin/bash", "-c"]
  }
}

resource "null_resource" "configure_bgp" {
  depends_on = [null_resource.install_requirements_for_bgp]

  provisioner "local-exec" {
    command     = ".venv/bin/python3 bgp_routing.py --fmc-url '${var.cdfmc_host}' --api-key '${var.scc_token}' --device-id '${var.devices[0].id}' --network-ids '${jsonencode(var.network_ids)}'"
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
