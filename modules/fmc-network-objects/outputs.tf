output "network_objects" {
  description = "Created network objects for OSPF configuration"
  value = {
    # apps        = fmc_network.apps
    apps        = data.fmc_network.apps
    attacker    = fmc_network.attacker
    data_center = fmc_network.data_center
    dmz         = fmc_network.dmz
    outside     = fmc_network.outside
    transport   = fmc_network.transport
  }
}

output "network_object_ids" {
  description = "Network object IDs for OSPF script usage"
  value = {
    # apps_id        = fmc_network.apps.id
    apps_id        = data.fmc_network.apps.id
    attacker_id    = fmc_network.attacker.id
    data_center_id = fmc_network.data_center.id
    dmz_id         = fmc_network.dmz.id
    outside_id     = fmc_network.outside.id
    transport_id   = fmc_network.transport.id
  }
}
