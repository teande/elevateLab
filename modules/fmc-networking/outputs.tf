output "networks" {
  description = "Created networks"
  value = {
    branch_evpn_overlay      = fmc_network.Branch-EVPN-Overlay-Main
    branch_evpn_underlay     = fmc_network.Branch-EVPN-Underlay
    branch_evpn_overlay_prod = fmc_network.Branch-EVPN-Overlay-PROD
    branch_evpn_overlay_iot  = fmc_network.Branch-EVPN-Overlay-IOT
  }
}

output "hosts" {
  description = "Created hosts"
  value = {
    en_cat8kv               = fmc_host.En-Cat8Kv
    branch_router           = fmc_host.BRANCH-SITE-105-ROUTER
    hq_c8kv                 = fmc_host.HQ-SITE10-CEDGE8Kv
    secure_access_bgp_peer1 = fmc_host.Secure_Access_BGP_Peer_1
    secure_access_bgp_peer2 = fmc_host.Secure_Access_BGP_Peer_2
  }
}

output "static_routes" {
  description = "Created static routes"
  value = {
    internet            = fmc_device_ipv4_static_route.route_to_internet
    branch_evpn         = fmc_device_ipv4_static_route.dc_branch_evpn_route
    branch_c8kv         = fmc_device_ipv4_static_route.dc_branch_c8kv_route
    hq_c8kv             = fmc_device_ipv4_static_route.dc_hq_c8kv_route
    prod_wan            = fmc_device_ipv4_static_route.route_to_prod_wan
    iot_wan             = fmc_device_ipv4_static_route.route_to_iot_wan
    secure_access_peer1 = fmc_device_ipv4_static_route.route_to_secure_access_peer1
    secure_access_peer2 = fmc_device_ipv4_static_route.route_to_secure_access_peer2
  }
}
