terraform state rm module.fmc_interface_groups.fmc_interface_group.netflow_managed
terraform state rm module.fmc_network_objects.fmc_network.attacker
terraform state rm module.fmc_network_objects.fmc_network.data_center
terraform state rm module.fmc_network_objects.fmc_network.dmz
terraform state rm module.fmc_network_objects.fmc_network.outside
terraform state rm module.fmc_network_objects.fmc_network.transport
terraform destroy -auto-approve