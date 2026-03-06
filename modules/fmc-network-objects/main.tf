terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

################################################################################################
# Network Objects for OSPF Configuration
################################################################################################

# resource "fmc_network" "apps" {
#   name        = "Apps"
#   prefix      = "198.18.11.0/24"
#   description = "Applications network segment"
# }

data "fmc_network" "apps" {
  name = "Apps"
}

resource "fmc_network" "attacker" {
  name        = "Attacker"
  prefix      = "198.18.14.0/24"
  description = "Attacker network segment"
}

resource "fmc_network" "data_center" {
  name        = "Data-Center"
  prefix      = "198.18.5.0/24"
  description = "Data center network segment"
}

resource "fmc_network" "dmz" {
  name        = "DMZ"
  prefix      = "198.18.9.0/24"
  description = "DMZ network segment"
}

resource "fmc_network" "outside" {
  name        = "Outside"
  prefix      = "198.18.3.0/24"
  description = "Outside network segment"
}

resource "fmc_network" "transport" {
  name        = "Transport"
  prefix      = "198.18.12.0/24"
  description = "Transport network segment"
}
