variable "ftd_ips" {
  description = "List of FTD IP addresses"
  type        = list(string)
}

variable "device_name" {
  description = "Device name for FTD"
  type        = list(string)
}

variable "policies" {
  type        = list(string)
  description = "Name of the imported ACPs"
  default     = ["HQ Firewall Policy"]
}

variable "cdfmc_host" {
  description = "CDO FMC host"
  type        = string
}

variable "scc_token" {
  description = "SCC token for device registration"
  type        = string
}

variable "scc_host" {
  description = "SCC host URL"
  type        = string
  default     = "https://us.manage.security.cisco.com"
}
