output "vti_interfaces" {
  description = "Discovered VTI interfaces"
  value = {
    vti_1 = data.fmc_device_virtual_tunnel_interface.WAN_static_vti_1
    vti_2 = data.fmc_device_virtual_tunnel_interface.WAN_static_vti_2
  }
}
