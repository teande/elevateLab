terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

################################################################################################
# Policy Assignments
################################################################################################

# DC Firewall Policy Assignments
resource "fmc_policy_assignment" "access_policy_assignments" {
  count       = length(var.device_names)
  policy_id   = var.access_policies[count.index].id
  policy_type = "AccessPolicy"
  targets = [
    {
      id   = var.devices[count.index].id
      type = "Device"
    }
  ]

  depends_on = [
    var.devices,
    var.access_policies
  ]
}

resource "fmc_policy_assignment" "dc_nat_policy" {
  policy_id   = var.nat_policy.id
  policy_type = "FTDNatPolicy"
  targets = [
    {
      id   = var.devices[0].id
      type = "Device"
    }
  ]

  depends_on = [
    var.devices,
    var.nat_policy
  ]
}

resource "null_resource" "platform_policy_assignment" {
  count = length(var.ftd_ips)
  triggers = {
    device_id = var.devices[0].id
    # run_every_time = timestamp()
  }

  provisioner "local-exec" {
    command     = ".venv/bin/python3 platsettings.py --host ${var.cdfmc_host} --token ${var.scc_token} --deviceid ${var.devices[count.index].id} --is_cdfmc 'true' --platformpolicy_name 'vFTD-platform-policy'"
    working_dir = "${path.module}/../../scripts/config-import"
    interpreter = ["/bin/bash", "-c"]
  }

  depends_on = [
    var.devices
  ]
}
