variable "cdfmc_host" {
  description = "CDO FMC host URL"
  type        = string
}

variable "scc_token" {
  description = "SCC API token for authentication"
  type        = string
  sensitive   = true
}

variable "device_name" {
  description = "FTD device name"
  type        = string
}

variable "devices" {
  description = "List of FTD devices (for dependency)"
  type        = any
  default     = []
}

variable "network_ids" {
  description = "Network object IDs for OSPF configuration"
  type        = map(string)
  default     = {}
}
