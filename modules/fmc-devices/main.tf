terraform {
  required_providers {
    cdo = {
      source = "CiscoDevnet/cdo"
    }
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

################################################################################################
# Security Zones — not present in base tenant being replicated; commented out until confirmed needed
################################################################################################
# resource "fmc_security_zone" "APPS" {
#   name           = "APPS"
#   interface_mode = "ROUTED"
# }

# resource "fmc_security_zone" "TUNNEL_ZONE" {
#   name           = "TUNNEL-ZONE"
#   interface_mode = "ROUTED"
# }

################################################################################
# Import the configurations
################################################################################
# Requires shared venv at scripts/.venv (created by deploy_prep_pod_configuration.sh)
resource "null_resource" "import_firewall_config" {
  provisioner "local-exec" {
    command     = "../.venv/bin/python3 main.py --host https://${var.cdfmc_host} --token ${var.scc_token} --backup-file automation.sfo"
    working_dir = "${path.root}/scripts/config-import"
    interpreter = ["/bin/bash", "-c"]
  }
}

resource "time_sleep" "wait_for_import" {
  depends_on      = [null_resource.import_firewall_config]
  create_duration = "2m"
}

################################################################################################
# Security Zone Data Sources
################################################################################################
data "fmc_security_zone" "WAN" {
  depends_on = [time_sleep.wait_for_import]
  name       = "WAN"
}

data "fmc_security_zone" "DMZ" {
  depends_on = [time_sleep.wait_for_import]
  name       = "DMZ"
}

data "fmc_security_zone" "INTERNET" {
  depends_on = [time_sleep.wait_for_import]
  name       = "INTERNET"
}

data "fmc_security_zone" "DATA-CENTER" {
  depends_on = [time_sleep.wait_for_import]
  name       = "DATA-CENTER"
}

data "fmc_security_zone" "SecureAccess" {
  depends_on = [time_sleep.wait_for_import]
  name       = "SecureAccess"
}

# data "fmc_ftd_nat_policy" "dc_firewall_nat_policy" {
#   depends_on = [time_sleep.wait_for_import]
#   name       = "HQ NAT Policy"
# }

################################################################################
# Device Onboarding
################################################################################
data "fmc_access_control_policy" "fmc_access_policy" {
  depends_on = [time_sleep.wait_for_import]
  count      = length(var.policies)
  name       = var.policies[count.index]
}

resource "cdo_ftd_device" "ngfw" {
  depends_on         = [time_sleep.wait_for_import]
  count              = length(var.ftd_ips)
  name               = var.device_name[count.index]
  licenses           = ["BASE", "MALWARE", "THREAT", "URLFilter"]
  virtual            = true
  performance_tier   = "FTDv10"
  access_policy_name = data.fmc_access_control_policy.fmc_access_policy[count.index].name

  lifecycle {
    ignore_changes = [
      access_policy_name
    ]
  }
}

resource "null_resource" "ftd_onboarding_script" {
  count = length(var.ftd_ips)

  triggers = {
    generated_command = cdo_ftd_device.ngfw[count.index].generated_command
    host_ip           = var.ftd_ips[count.index]
  }

  provisioner "local-exec" {
    command     = "../.venv/bin/python3 cdo.py --host ${self.triggers.host_ip} --username admin --password dCloud123! --gen_command '${self.triggers.generated_command}'"
    working_dir = "${path.root}/scripts/device-onboarding"
    interpreter = ["/bin/bash", "-c"]
  }
}

resource "cdo_ftd_device_onboarding" "ftd_onboarding" {
  count      = length(var.ftd_ips)
  depends_on = [null_resource.ftd_onboarding_script]
  ftd_uid    = cdo_ftd_device.ngfw[count.index].id
}

resource "time_sleep" "wait_for_onboarding" {
  depends_on      = [cdo_ftd_device_onboarding.ftd_onboarding]
  create_duration = "2m"
}

################################################################################################
# Devices Data Sources
################################################################################################
data "fmc_device" "devices" {
  depends_on = [time_sleep.wait_for_onboarding]
  count      = length(var.ftd_ips)
  name       = var.device_name[count.index]
}
