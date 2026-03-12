terraform {
  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

################################################################################################
# VPN Site-to-Site Tunnels
################################################################################################

# SecureAccess VPN Site-to-Site Tunnel
resource "fmc_vpn_s2s" "secure_access" {
  name             = "SecureAccess"
  route_based      = true
  network_topology = "POINT_TO_POINT"
  ikev1            = false
  ikev2            = true
}

################################################################################################
# IKEv2 Settings
################################################################################################

resource "fmc_vpn_s2s_ike_settings" "ike_settings" {
  vpn_s2s_id                             = fmc_vpn_s2s.secure_access.id
  ikev2_authentication_type              = "MANUAL_PRE_SHARED_KEY"
  ikev2_manual_pre_shared_key            = "dCloud123!"
  ikev2_enforce_hex_based_pre_shared_key = false

  depends_on = [fmc_vpn_s2s.secure_access]
}

################################################################################################
# VPN S2S Endpoints
################################################################################################

resource "fmc_vpn_s2s_endpoints" "endpoints" {
  vpn_s2s_id = fmc_vpn_s2s.secure_access.id

  items = {
    # Node A - Internal FTD device
    internal_node = {
      peer_type                    = "PEER"
      extranet_device              = false
      device_id                    = var.devices[0].id
      interface_id                 = var.vti_interfaces.vti_1.id
      local_identity_type          = "EMAILID"
      local_identity_string        = "change_me@cisco.com"
      backup_interface_id          = var.vti_interfaces.vti_2.id
      backup_local_identity_type   = "EMAILID"
      backup_local_identity_string = "change_me@cisco.com"
      connection_type              = "BIDIRECTIONAL"
      allow_incoming_ikev2_routes  = true
    }

    # Node B - Extranet SecureAccess cloud device
    SecureAccess = {
      peer_type                   = "PEER"
      extranet_device             = true
      extranet_dynamic_ip         = false
      extranet_ip_address         = "44.217.195.188,35.171.214.188"
      connection_type             = "BIDIRECTIONAL"
      allow_incoming_ikev2_routes = true
    }
  }

  depends_on = [
    fmc_vpn_s2s.secure_access,
    fmc_vpn_s2s_ike_settings.ike_settings,
    var.devices,
    var.vti_interfaces
  ]
}


resource "fmc_device_deploy" "deploy" {
  depends_on      = [fmc_vpn_s2s_endpoints.endpoints]
  ignore_warning  = true
  device_id_list  = [var.devices[0].id]
  deployment_note = "Terraform initiated deployment"
}
