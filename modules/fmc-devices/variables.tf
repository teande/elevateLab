variable "ftd_ips" {
  type        = list(string)
  description = "IPs of the FTDs"
}

variable "device_name" {
  type        = list(string)
  description = "Names of the FTD devices"
}

variable "policies" {
  type        = list(string)
  description = "Name of the imported ACPs"
}

variable "cdfmc_host" {
  type        = string
  description = "cdFMC URL"
}

variable "scc_token" {
  type        = string
  description = "CDO Token"
}
