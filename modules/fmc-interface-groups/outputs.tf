output "inside_nets_group" {
  description = "INSIDE_NETS interface group"
  value       = fmc_interface_group.inside_nets
}

output "inside_nets_group_id" {
  description = "INSIDE_NETS interface group ID"
  value       = fmc_interface_group.inside_nets.id
}

output "netflow_managed_group" {
  description = "Managed NetFlowGrp interface group"
  value       = fmc_interface_group.netflow_managed
}

output "netflow_managed_group_id" {
  description = "Managed NetFlowGrp interface group ID"
  value       = fmc_interface_group.netflow_managed.id
}
