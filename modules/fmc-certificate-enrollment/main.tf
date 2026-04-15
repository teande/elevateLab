terraform {
  required_providers {
    cdo = {
      source = "CiscoDevnet/cdo"
    }
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.1"
    }
  }
}

resource "fmc_certificate_enrollment" "device_certificate" {
  name                          = var.pkcs12_cert_name
  description                   = "PKCS12 certificate enrollment object in FMC"
  enrollment_type               = "PKCS12"
  pkcs12_certificate            = filebase64(var.pkcs12_cert_path)
  pkcs12_certificate_passphrase = var.pkcs12_passphrase
  validation_usage_ipsec_client = true
  validation_usage_ssl_server   = true
  validation_usage_ssl_client   = true
  skip_ca_flag_check            = false
  # CRL and OCSP are both disabled — API requires this to be true or it rejects the request
  consider_certificate_valid_if_revocation_information_not_reachable = true
}

resource "fmc_certificate_enrollment" "root_ca" {
  name            = "Pseudoco_Root_CA"
  description     = "Root CA enrollment"
  enrollment_type = "MANUAL"
  # NOTE: The FMC provider API only supports CA-only mode for MANUAL enrollment.
  # "Manual (CA & ID)" is not exposed by the API — manual_ca_only must be true.
  manual_ca_only                                                     = true
  manual_ca_certificate                                              = filebase64(var.root_ca_cert_path)
  validation_usage_ipsec_client                                      = true
  validation_usage_ssl_server                                        = false
  validation_usage_ssl_client                                        = true
  skip_ca_flag_check                                                 = false
  consider_certificate_valid_if_revocation_information_not_reachable = true
  crl_use_distribution_point_from_the_certificate                    = true
}

resource "fmc_trusted_certificate_authority" "trusted_root_ca" {
  name        = "trusted_pseudoco_root_ca"
  # Normalize line endings: .cer files with CRLF (\r\n) cause the FMC cert parser to reject the chain
  certificate = replace(file(var.root_ca_cert_path), "\r\n", "\n")
}
