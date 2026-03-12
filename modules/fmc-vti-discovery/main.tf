terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

################################################################################################
# VTI Interface Discovery - Data Sources Only
# This module discovers existing VTI interfaces without trying to manage them
################################################################################################

# Discover existing VTI interface: Tunnel1 (WAN_static_vti_1)
data "fmc_device_vti_interface" "WAN_static_vti_1" {
  device_id = var.devices[0].id
  name      = "Tunnel1"

  depends_on = [var.devices]
}

# Discover existing VTI interface: Tunnel2 (WAN_static_vti_2)
data "fmc_device_vti_interface" "WAN_static_vti_2" {
  device_id = var.devices[0].id
  name      = "Tunnel2"

  depends_on = [var.devices]
}
