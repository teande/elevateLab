output "vpn_tunnels" {
  description = "VPN S2S tunnels"
  value = {
    secure_access = fmc_vpn_s2s.secure_access
  }
}

output "ike_settings" {
  description = "IKE settings"
  value       = fmc_vpn_s2s_ike_settings.ike_settings
}

output "endpoints" {
  description = "VPN endpoints"
  value = {
    endpoints = fmc_vpn_s2s_endpoints.endpoints
  }
}
