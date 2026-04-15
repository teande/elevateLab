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

variable "pkcs12_cert_name" {
  description = "Name for the PKCS12 certificate enrollment object in FMC"
  type        = string
  default     = "pseudoco-device-cert"
}

variable "pkcs12_cert_path" {
  description = "Path to the PKCS12 (.p12 / .pkcs12) certificate file"
  type        = string
  default     = "./certs/pseudoco-cert.p12"
}

variable "pkcs12_passphrase" {
  description = "Passphrase protecting the PKCS12 file"
  type        = string
  sensitive   = true
}

variable "root_ca_cert_path" {
  description = "Path to the root CA certificate file (.cer / .pem)"
  type        = string
  default     = "./certs/pseudoco-rootca.cer"
}
