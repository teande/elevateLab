terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

################################################################################################
# Platform Settings Policy Data Source
################################################################################################

data "fmc_ftd_platform_settings" "platform_policy" {
  name = "vFTD-platform-policy"
}

################################################################################################
# Policy Assignments
################################################################################################

# DC Firewall Access Policy Assignments
resource "fmc_policy_assignment" "access_policy_assignments" {
  count       = length(var.device_names)
  policy_id   = var.access_policies[count.index].id
  policy_type = "AccessPolicy"
  targets = [
    {
      id   = var.devices[count.index].id
      type = "Device"
      name = var.device_names[count.index]
    }
  ]

  depends_on = [
    var.devices,
    var.access_policies
  ]
}

# NAT policy not present in base tenant being replicated
# resource "fmc_policy_assignment" "dc_nat_policy" {
#   policy_id   = var.nat_policy.id
#   policy_type = "FTDNatPolicy"
#   targets = [
#     {
#       id   = var.devices[0].id
#       type = "Device"
#       name = var.device_names[0]
#     }
#   ]
#
#   depends_on = [
#     var.devices,
#     var.nat_policy
#   ]
# }

# Platform Settings Policy Assignment
resource "fmc_policy_assignment" "platform_policy_assignments" {
  count       = length(var.device_names)
  policy_id   = data.fmc_ftd_platform_settings.platform_policy.id
  policy_type = "FTDPlatformSettingsPolicy"
  targets = [
    {
      id   = var.devices[count.index].id
      type = "Device"
      name = var.device_names[count.index]
    }
  ]

  depends_on = [
    var.devices,
  ]
}
