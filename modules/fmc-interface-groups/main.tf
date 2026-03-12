terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

################################################################################################
# Interface Groups Configuration
################################################################################################

# INSIDE_NETS not required in new lab tenant — commented out
# resource "fmc_interface_group" "inside_nets" {
#   name           = "INSIDE_NETS"
#   interface_mode = "ROUTED"
#   interfaces     = var.inside_interfaces
# }

# Manage existing NetFlowGrp interface group (will be imported by deploy script)
resource "fmc_interface_group" "netflow_managed" {
  name           = "NetFlowGrp"
  interface_type = "ROUTED"
  interfaces     = var.netflow_interfaces
}
