terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

################################################################################################
# Network objects Data objects
################################################################################################
data "fmc_network" "ipv4-private-10_0_0_0-8" {
  name = "IPv4-Private-10.0.0.0-8"
}

data "fmc_network" "any-ipv4" {
  name = "any-ipv4"
}

# ExtGW: imported via .sfo — look up as data source
data "fmc_host" "ExtGW" {
  name = "ExtGW"
}

################################################################################################
# Network Object Resources
################################################################################################
resource "fmc_network" "Branch-EVPN-Overlay-Main" {
  depends_on  = [var.devices]
  name        = "Branch-EVPN-Overlay-Main"
  prefix      = "10.10.255.0/24"
  description = "Main branch EVPN overlay network"
}

resource "fmc_network" "Branch-EVPN-Underlay" {
  depends_on  = [var.devices]
  name        = "Branch-EVPN-Underlay"
  prefix      = "172.30.255.0/24"
  description = "Branch EVPN underlay network"
}

resource "fmc_network" "Branch-EVPN-Overlay-PROD" {
  depends_on  = [var.devices]
  name        = "Branch-EVPN-Overlay-PROD"
  prefix      = "10.101.255.0/24"
  description = "PROD branch EVPN overlay network"
}

resource "fmc_network" "Branch-EVPN-Overlay-IOT" {
  depends_on  = [var.devices]
  name        = "Branch-EVPN-Overlay-IOT"
  prefix      = "10.102.255.0/24"
  description = "IOT branch EVPN overlay network"
}

################################################################################################
# Host Object Resources
################################################################################################
resource "fmc_host" "En-Cat8Kv" {
  name = "En-Cat8Kv"
  ip   = "198.18.8.1"
}

resource "fmc_host" "BRANCH-SITE-105-ROUTER" {
  name = "BRANCH-SITE-105-ROUTER"
  ip   = "100.100.10.105"
}

resource "fmc_host" "HQ-SITE10-CEDGE8Kv" {
  name = "HQ-SITE10-CEDGE8Kv"
  ip   = "100.100.10.10"
}

resource "fmc_host" "Secure_Access_BGP_Peer_1" {
  name = "Secure_Access_BGP_Peer_1"
  ip   = "169.254.0.5"
}

resource "fmc_host" "Secure_Access_BGP_Peer_2" {
  name = "Secure_Access_BGP_Peer_2"
  ip   = "169.254.0.9"
}

################################################################################################
# DC Firewall Static Routes
################################################################################################

# Internet default route
resource "fmc_device_ipv4_static_route" "route_to_internet" {
  device_id              = var.devices[0].id
  interface_logical_name = "INTERNET"
  interface_id           = var.physical_interfaces[2].id
  destination_networks = [{
    id = data.fmc_network.any-ipv4.id
  }]
  gateway_host_object_id = data.fmc_host.ExtGW.id

  depends_on = [
    var.devices,
    var.physical_interfaces,
    data.fmc_host.ExtGW
  ]
}

# Main-WAN: Branch EVPN overlay + underlay
resource "fmc_device_ipv4_static_route" "dc_branch_evpn_route" {
  device_id              = var.devices[0].id
  interface_logical_name = "Main-WAN"
  interface_id           = var.physical_interfaces[0].id
  destination_networks = [{
    id = fmc_network.Branch-EVPN-Overlay-Main.id
    }, {
    id = fmc_network.Branch-EVPN-Underlay.id
  }]
  gateway_host_literal = "198.18.8.0"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.physical_interfaces,
    fmc_network.Branch-EVPN-Overlay-Main,
    fmc_network.Branch-EVPN-Underlay
  ]
}

# Main-WAN: Branch site 105 router
resource "fmc_device_ipv4_static_route" "dc_branch_c8kv_route" {
  device_id              = var.devices[0].id
  interface_logical_name = "Main-WAN"
  interface_id           = var.physical_interfaces[0].id
  destination_networks = [{
    id = fmc_host.BRANCH-SITE-105-ROUTER.id
  }]
  gateway_host_literal = "198.18.8.0"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.physical_interfaces,
    fmc_host.BRANCH-SITE-105-ROUTER
  ]
}

# Main-WAN: HQ CEDGE 8Kv
resource "fmc_device_ipv4_static_route" "dc_hq_c8kv_route" {
  device_id              = var.devices[0].id
  interface_logical_name = "Main-WAN"
  interface_id           = var.physical_interfaces[0].id
  destination_networks = [{
    id = fmc_host.HQ-SITE10-CEDGE8Kv.id
  }]
  gateway_host_literal = "198.18.8.0"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.physical_interfaces,
    fmc_host.HQ-SITE10-CEDGE8Kv
  ]
}

# PROD-WAN: Branch EVPN overlay PROD
resource "fmc_device_ipv4_static_route" "route_to_prod_wan" {
  device_id              = var.devices[0].id
  interface_logical_name = "PROD-WAN"
  interface_id           = var.physical_interfaces[4].id
  destination_networks = [{
    id = fmc_network.Branch-EVPN-Overlay-PROD.id
  }]
  gateway_host_literal = "198.18.8.2"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.physical_interfaces,
    fmc_network.Branch-EVPN-Overlay-PROD
  ]
}

# IOT-WAN: Branch EVPN overlay IOT
resource "fmc_device_ipv4_static_route" "route_to_iot_wan" {
  device_id              = var.devices[0].id
  interface_logical_name = "IOT-WAN"
  interface_id           = var.physical_interfaces[5].id
  destination_networks = [{
    id = fmc_network.Branch-EVPN-Overlay-IOT.id
  }]
  gateway_host_literal = "198.18.8.4"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.physical_interfaces,
    fmc_network.Branch-EVPN-Overlay-IOT
  ]
}

# WAN_static_vti_1: Secure Access BGP Peer 1
resource "fmc_device_ipv4_static_route" "route_to_secure_access_peer1" {
  device_id              = var.devices[0].id
  interface_logical_name = "WAN_static_vti_1"
  interface_id           = var.vti_interfaces.vti_1.id
  destination_networks = [{
    id = fmc_host.Secure_Access_BGP_Peer_1.id
  }]
  gateway_host_literal = "169.254.6.1"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.vti_interfaces,
    fmc_host.Secure_Access_BGP_Peer_1
  ]
}

# WAN_static_vti_2: Secure Access BGP Peer 2
resource "fmc_device_ipv4_static_route" "route_to_secure_access_peer2" {
  device_id              = var.devices[0].id
  interface_logical_name = "WAN_static_vti_2"
  interface_id           = var.vti_interfaces.vti_2.id
  destination_networks = [{
    id = fmc_host.Secure_Access_BGP_Peer_2.id
  }]
  gateway_host_literal = "169.254.6.5"
  metric_value         = 1

  depends_on = [
    var.devices,
    var.vti_interfaces,
    fmc_host.Secure_Access_BGP_Peer_2
  ]
}
