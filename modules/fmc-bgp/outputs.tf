output "bgp_configuration_status" {
  description = "BGP configuration completion status"
  value       = "BGP configuration applied"
  depends_on  = [null_resource.configure_bgp]
}
