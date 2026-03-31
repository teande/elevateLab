# Elevate Lab — FMC Infrastructure Automation

Terraform automation for configuring Cisco Firepower Management Center (FMC) lab environments. Targets a cloud-delivered FMC (cdFMC) instance managed through Cisco Defense Orchestrator (CDO/SCC).

## Overview

The automation handles the full lifecycle of a lab pod:

- **Device onboarding**: Registers the FTD with CDO, imports base configuration from `.sfo` backup
- **Interface configuration**: 7 physical interfaces + 2 VTI tunnel interfaces with security zones
- **Network objects and static routes**: Branch EVPN networks, host objects, 8 static routes
- **Policy assignments**: Access control policy + platform policy assigned to the device
- **OSPF**: Process 1 / Area 0 via Python REST API
- **BGP**: AS 65532, neighbors via Tunnel1/Tunnel2 to Secure Access
- **VPN**: Single IKEv2 site-to-site tunnel (SecureAccess)

## Providers

| Provider | Version |
| -------- | ------- |
| `CiscoDevNet/fmc` | 2.0.1 |
| `CiscoDevnet/cdo` | latest |

## Module Execution Order

```
fmc-devices → fmc-vti-discovery → fmc-interfaces → fmc-interface-groups
    → fmc-networking → fmc-network-objects → fmc-policies → fmc-ospf → fmc-bgp → fmc-vpn
```

VPN module always runs last. Never reorder without understanding the full `depends_on` chain.

## Module Reference

| Module | Purpose |
| ------ | ------- |
| `fmc-devices` | `.sfo` config import, CDO device registration, SSH onboarding |
| `fmc-vti-discovery` | Data sources — discovers Tunnel1 and Tunnel2 interface IDs |
| `fmc-interfaces` | Physical (G0/0–G0/6) and VTI interface config with zone assignment |
| `fmc-interface-groups` | Manages pre-existing `NetFlowGrp` (imported by deploy) |
| `fmc-networking` | Network objects, host objects, 8 static routes |
| `fmc-network-objects` | OSPF-specific network objects |
| `fmc-policies` | ACP + platform policy assignments (native `fmc_policy_assignment`) |
| `fmc-ospf` | OSPF Process 1 / Area 0 via Python REST API |
| `fmc-bgp` | BGP AS 65532 via Python REST API |
| `fmc-vpn` | IKEv2 site-to-site: SecureAccess |

## Interface Layout

| Interface | Logical Name | IP | Zone |
| --------- | ------------ | -- | ---- |
| G0/0 | Main-WAN | 198.18.8.1/31 | WAN |
| G0/1 | DMZ | 198.18.9.1/24 | DMZ |
| G0/2 | INTERNET | 198.18.3.2/24 | INTERNET |
| G0/3 | DATA-CENTER | 198.18.5.1/24 | DATA-CENTER |
| G0/4 | PROD-WAN | 198.18.8.3/31 | WAN |
| G0/5 | IOT-WAN | 198.18.8.5/31 | WAN |
| G0/6 | APP | 198.18.11.1/24 | — |
| Tunnel1 | WAN_static_vti_1 | 169.254.6.2/30 | SecureAccess |
| Tunnel2 | WAN_static_vti_2 | 169.254.6.6/30 | SecureAccess |

VTI interfaces (Tunnel1, Tunnel2) are **imported** into state by the deploy script — not created fresh.

## Prerequisites

- **Terraform** >= 1.0
- **Python 3** with `pip`
- Access to a cdFMC tenant and CDO/SCC API token

## Configuration

Copy `terraform.tfvars.ignore` to `terraform.tfvars` and fill in:

```hcl
scc_token  = "your-scc-api-token"
scc_host   = "https://eu.manage.security.cisco.com"   # match your region
cdfmc_host = "your-cdfmc-hostname.cisco.com"

# Pre-configured for lab — change only if your pod differs
ftd_ips     = ["198.18.133.39"]
device_name = ["hqftdv"]
policies    = ["HQ Firewall Policy"]
```

`terraform.tfvars` and `*.tfstate` are gitignored — never commit them.

## Deploying

```bash
./cli.py deploy
```

The deploy script is fully automated and self-bootstrapping (creates the Python venv automatically). It runs 11 steps:

1. `terraform init`
2. Python venv ready
3. FTD device registration (`module.fmc_devices`)
4. VTI discovery (`module.fmc_vti_discovery`)
5. ID extraction (device ID, VTI IDs, NetFlowGrp ID)
6. VTI interface import into state (always rm-then-import for idempotency)
7. NetFlowGrp import into state
8. Core configuration (interfaces, networking, objects, groups, policies)
9. OSPF configuration
10. BGP configuration
11. VPN configuration

Progress is cached in `.pod_prepare_progress` and `.vti_ids_cache`. Delete these files to force a full re-run.

## Resetting Between Sessions

```bash
./cli.py reset
```

Cleans the cdFMC tenant and Terraform state so the next `./cli.py deploy` runs cleanly against a fresh pod. Sequence:

1. Deletes the `SecureAccess` S2S VPN topology from FMC
2. Deregisters the FTD from CDO and polls until gone
3. Deletes the `HQ Firewall Policy` ACP (re-imported from `.sfo` on next deploy)
4. Clears all device-scoped Terraform state
5. Clears deploy cache files

## Destroying

```bash
./cli.py destroy
```

Removes OSPF-managed network objects and pre-imported resources from state first, then runs `terraform destroy`.

## Common Commands

```bash
# Deploy a specific module
terraform apply -target=module.fmc_interfaces

# View current state
terraform state list

# Remove a resource from state before re-importing
terraform state rm module.fmc_interface_groups.fmc_interface_group.netflow_managed

# Force re-run of deploy from scratch
rm -f .pod_prepare_progress .vti_ids_cache
./cli.py deploy

# Enable debug logging
export TF_LOG=DEBUG
terraform apply
```

## Troubleshooting

**Device registration fails / ACP not found**
The deploy script expects the `.sfo` import to complete and the ACP to exist before registering the device. If the previous session's ACP is missing, run `./cli.py reset` first to ensure a clean state.

**VTI import fails**
VTI IDs are tied to the device. After a reset, the old IDs are stale. The deploy script always removes stale VTI state before importing (`rm-then-import` pattern). If it fails, delete `.vti_ids_cache` and re-run.

**OSPF/BGP not applying**
These are Python null_resource triggers. If the device ID changed (after a reset), they will re-run automatically on the next deploy.

**State out of sync after manual operations**
```bash
terraform state list       # see what's in state
terraform state rm <addr>  # remove a stale entry
```

## Python Scripts

All scripts share a single venv at `scripts/.venv/` (created automatically by `cli.py`).

| Script | Purpose |
| ------ | ------- |
| `scripts/config-import/main.py` | Imports `.sfo` config backup to cdFMC via REST API |
| `scripts/device-onboarding/cdo.py` | SSH automation for CDO registration command |
| `scripts/ospf/cdfmc_ospf_automation.py` | Configures OSPF via FMC REST API |
| `scripts/bgp/bgp_routing.py` | Configures BGP via FMC REST API |
| `scripts/reset/reset.py` | Tenant cleanup between sessions |

## Provider Documentation

- [CiscoDevNet/fmc Terraform provider](https://registry.terraform.io/providers/CiscoDevNet/fmc/latest/docs)
- [CiscoDevnet/cdo Terraform provider](https://registry.terraform.io/providers/CiscoDevnet/cdo/latest/docs)
- [FMC REST API reference](https://developer.cisco.com/docs/fmc-rest-api/)
- [CDO API reference](https://developer.cisco.com/docs/cisco-security-cloud-control-firewall-manager/)

---

**FMC Provider**: 2.0.1 | **Terraform**: >= 1.0
