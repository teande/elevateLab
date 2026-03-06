terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

################################################################################################
# Interface Groups Configuration
################################################################################################

# Create new INSIDE_NETS interface group
resource "fmc_interface_group" "inside_nets" {
  name           = "INSIDE_NETS"
  interface_mode = "ROUTED"
  interfaces     = var.inside_interfaces
}

# Manage existing NetFlowGrp interface group (will be imported by deploy script)
resource "fmc_interface_group" "netflow_managed" {
  name           = "NetFlowGrp"
  interface_mode = "ROUTED"
  interfaces     = var.netflow_interfaces
}
