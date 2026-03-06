terraform {
  required_providers {
    cdo = {
      source = "CiscoDevnet/cdo"
    }
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "2.0.0-rc4"
    }
  }
}

provider "cdo" {
  api_token = var.scc_token
  base_url  = var.scc_host
}

provider "fmc" {
  url   = "https://${var.cdfmc_host}"
  token = var.scc_token
}
