output "devices" {
  description = "FMC devices"
  value       = data.fmc_device.devices
}

output "wait_for_onboarding" {
  description = "Wait for onboarding completion"
  value       = time_sleep.wait_for_onboarding
}

output "security_zones" {
  description = "Security zones"
  value = {
    WAN          = data.fmc_security_zone.WAN
    DMZ          = data.fmc_security_zone.DMZ
    INTERNET     = data.fmc_security_zone.INTERNET
    DATA_CENTER  = data.fmc_security_zone.DATA-CENTER
    SecureAccess = data.fmc_security_zone.SecureAccess
    # APPS and TUNNEL_ZONE are not present in base tenant — commented out
  }
}

output "access_policies" {
  description = "Access control policies"
  value       = data.fmc_access_control_policy.fmc_access_policy
}

# NAT policy not present in base tenant being replicated
# output "nat_policy" {
#   description = "NAT policy"
#   value       = data.fmc_ftd_nat_policy.dc_firewall_nat_policy
# }
