output "physical_interfaces" {
  description = "Physical interfaces data"
  value       = data.fmc_device_physical_interface.dc_phy_interfaces
}

output "created_vti_interfaces" {
  description = "Created VTI interfaces"
  value = {
    WAN_static_vti_1 = fmc_device_vti_interface.WAN_static_vti_1
    WAN_static_vti_2 = fmc_device_vti_interface.WAN_static_vti_2
  }
}

output "created_interfaces" {
  description = "Created physical interfaces"
  value = {
    dc_g0_0 = fmc_device_physical_interface.dc_g0_0
    dc_g0_1 = fmc_device_physical_interface.dc_g0_1
    dc_g0_2 = fmc_device_physical_interface.dc_g0_2
    dc_g0_3 = fmc_device_physical_interface.dc_g0_3
    dc_g0_4 = fmc_device_physical_interface.dc_g0_4
    dc_g0_5 = fmc_device_physical_interface.dc_g0_5
    dc_g0_6 = fmc_device_physical_interface.dc_g0_6
  }
}
