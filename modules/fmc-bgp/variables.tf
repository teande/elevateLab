variable "cdfmc_host" {
  description = "cdFMC hostname (no https://)"
  type        = string
}

variable "scc_token" {
  description = "SCC API token for authentication"
  type        = string
  sensitive   = true
}

variable "devices" {
  description = "List of FTD devices (for dependency and device ID)"
  type        = any
  default     = []
}

variable "network_ids" {
  description = "Network object IDs for BGP advertised networks (name → UUID)"
  type        = map(string)
  default     = {}
}
