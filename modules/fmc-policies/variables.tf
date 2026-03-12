variable "devices" {
  description = "FMC devices"
}

variable "access_policies" {
  description = "Access control policies"
}

# NAT policy not present in base tenant being replicated
# variable "nat_policy" {
#   description = "NAT policy"
# }

variable "device_names" {
  description = "Device names"
}
