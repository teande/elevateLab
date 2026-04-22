variable "pkcs12_cert_name" {
  type        = string
  description = "Name for the PKCS12 certificate enrollment object in FMC"
  default     = "pseudoco-device-cert"
}

variable "pkcs12_cert_path" {
  type        = string
  description = "Path to the PKCS12 (.p12 / .pkcs12) certificate file"
  sensitive   = true
}

variable "pkcs12_passphrase" {
  type        = string
  description = "Passphrase protecting the PKCS12 file"
  sensitive   = true
}

variable "root_ca_cert_path" {
  type        = string
  description = "Path to the root CA certificate file (.cer / .pem)"
  sensitive   = true
}
