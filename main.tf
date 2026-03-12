################################################################################################
# FMC Challenge Lab Infrastructure
################################################################################################

# Import configurations and wait for onboarding
module "fmc_devices" {
  source = "./modules/fmc-devices"

  # Pass variables
  ftd_ips     = var.ftd_ips
  device_name = var.device_name
  policies    = var.policies
  cdfmc_host  = var.cdfmc_host
  scc_token   = var.scc_token
}

# Discover existing VTI interfaces (data sources only)
module "fmc_vti_discovery" {
  source = "./modules/fmc-vti-discovery"

  # Dependencies
  depends_on = [module.fmc_devices.wait_for_onboarding]

  # Data from devices module
  devices = module.fmc_devices.devices
}

# Configure physical interfaces and VTI interfaces (after import)
module "fmc_interfaces" {
  source = "./modules/fmc-interfaces"

  # Dependencies - discovery must complete first
  depends_on = [module.fmc_vti_discovery]

  # Data from devices module
  devices             = module.fmc_devices.devices
  wait_for_onboarding = module.fmc_devices.wait_for_onboarding
  security_zones      = module.fmc_devices.security_zones
}

# Configure interface groups (after interfaces are created)
module "fmc_interface_groups" {
  source = "./modules/fmc-interface-groups"

  # Dependencies - interfaces must be created first
  depends_on = [module.fmc_interfaces]

  # Interface data for INSIDE_NETS group — commented out, not required in new lab tenant
  # inside_interfaces = [
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_0.id },
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_1.id },
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_2.id },
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_3.id },
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_4.id },
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_5.id },
  #   { id = module.fmc_interfaces.created_interfaces.dc_g0_6.id }
  # ]

  # Interface to add to NetFlowGrp (if managing it)
  netflow_interfaces = [{ id = module.fmc_interfaces.created_interfaces.dc_g0_3.id }]
}

# Configure networking (networks, hosts, static routes)
module "fmc_networking" {
  source = "./modules/fmc-networking"

  # Dependencies
  depends_on = [module.fmc_interface_groups]

  # Data from previous modules
  devices             = module.fmc_devices.devices
  physical_interfaces = module.fmc_interfaces.physical_interfaces
  vti_interfaces      = module.fmc_vti_discovery.vti_interfaces
  wait_for_onboarding = module.fmc_devices.wait_for_onboarding
}

# Configure network objects for OSPF
module "fmc_network_objects" {
  source = "./modules/fmc-network-objects"

  # Dependencies
  depends_on = [module.fmc_networking]

  # Data from previous modules
  devices = module.fmc_devices.devices
}

# Configure policy assignments
module "fmc_policies" {
  source = "./modules/fmc-policies"

  # Dependencies
  depends_on = [module.fmc_network_objects]

  # Data from previous modules
  devices         = module.fmc_devices.devices
  access_policies = module.fmc_devices.access_policies
  # nat_policy not present in base tenant being replicated
  # nat_policy      = module.fmc_devices.nat_policy
  device_names = var.device_name
}

# Configure OSPF (runs after policies but before BGP and VPN)
module "fmc_ospf" {
  source = "./modules/fmc-ospf"

  # Dependencies - OSPF runs after policies are configured
  depends_on = [module.fmc_policies]

  # Configuration parameters
  cdfmc_host  = var.cdfmc_host
  scc_token   = var.scc_token
  device_name = var.device_name[0] # Use first device name
  devices     = module.fmc_devices.devices
  network_ids = module.fmc_network_objects.network_object_ids
}

# Configure BGP (runs after OSPF, before VPN)
module "fmc_bgp" {
  source = "./modules/fmc-bgp"

  # Dependencies - BGP runs after OSPF
  depends_on = [module.fmc_ospf]

  # Configuration parameters
  cdfmc_host = var.cdfmc_host
  scc_token  = var.scc_token
  devices    = module.fmc_devices.devices
  network_ids = {
    # BGP script expects FMC object name as the key, not the Terraform output key (data_center_id)
    "Data-Center" = module.fmc_network_objects.network_object_ids.data_center_id
  }
}

# Configure VPN Site-to-Site (ALWAYS RUNS LAST)
module "fmc_vpn" {
  source = "./modules/fmc-vpn"

  # Dependencies - VPN runs last after BGP is configured
  depends_on = [module.fmc_bgp]

  # Data from previous modules
  devices        = module.fmc_devices.devices
  vti_interfaces = module.fmc_vti_discovery.vti_interfaces
}

