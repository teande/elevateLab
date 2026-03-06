output "ospf_configuration_status" {
  description = "Status of OSPF configuration"
  value       = "OSPF configuration completed successfully"
  depends_on  = [null_resource.configure_ospf]
}
