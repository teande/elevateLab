# Cisco FMC Challenge Lab Infrastructure

This project provides a complete Terraform-based automation solution for configuring Cisco Firepower Management Center (FMC) lab environments, specifically designed for challenge labs and training environments.

## 🎯 Project Overview

This infrastructure automation handles:
- **Device Onboarding**: Automated FTD device registration and configuration import
- **Interface Management**: Physical and VTI interface configuration with security zones
- **Network Configuration**: Static routes, network objects, and hosts
- **Policy Management**: Access control and NAT policy assignments
- **OSPF Configuration**: Dynamic routing protocol setup
- **Multi-Cloud Defense**: MCD policy integration
- **VPN Tunnels**: Site-to-site VPN configurations to AWS and secure access

## 🏗️ Architecture

The project uses a modular Terraform architecture with the following execution flow:

```
1. Device Registration & Config Import
2. VTI Interface Discovery
3. Physical & VTI Interface Configuration
4. Interface Group Management
5. Network Objects & Static Routes
6. Policy Assignments
7. OSPF Configuration
8. VPN Site-to-Site Setup (Always Last)
```

## 📋 Prerequisites

### Required Software
- **Terraform** >= 1.0
- **Python 3.x** with `pip`
- **Bash shell** (macOS/Linux)

### Required Credentials
- **CDO/SCC Token**: For device management and API access
- **cdFMC Host**: Your cloud FMC instance hostname
- **FTD Device Access**: SSH credentials for device onboarding

### Cisco Environment
- **cdFMC Instance**: Cloud-delivered FMC with API access
- **FTD Device**: Virtual or physical FTD ready for onboarding
- **Network Connectivity**: Lab network access for device management

## 🚀 Quick Start

### 1. Set Required Variables

Edit `terraform.tfvars`:
```hcl
scc_token  = "your-scc-token-here"
scc_host   = "https://us.manage.security.cisco.com"  # or your region
cdfmc_host = "your-cdfmc-hostname.cisco.com"

# Pre-configured (don't change unless needed)
ftd_ips     = ["198.18.133.30"]
device_name = ["HQ_FTDv"]
policies    = ["HQ Firewall Policy"]
```

### 2. Deploy Infrastructure

**Automated Deployment (Recommended)**
```bash
./deploy_prep_pod_configuration.sh
```

> **💡 Tip**: You can also deploy specific modules individually using Terraform:
> ```bash
> terraform init
> terraform apply -target=module.fmc_devices
> terraform apply -target=module.fmc_ospf
> ```

### 3. Clean Up

```bash
./destroy.sh
```

## 📁 Project Structure

```
challengeLab-clean/
├── main.tf                           # Main Terraform configuration
├── variables.tf                      # Variable definitions
├── terraform.tfvars                  # Configuration values
├── provider.tf                       # Provider configurations
├── deploy_prep_pod_configuration.sh  # Automated deployment script
├── destroy.sh                        # Cleanup script
├── modules/                          # Terraform modules
│   ├── fmc-devices/                  # Device registration & config import
│   ├── fmc-vti-discovery/            # VTI interface discovery
│   ├── fmc-interfaces/               # Physical & VTI interface config
│   ├── fmc-interface-groups/         # Interface group management
│   ├── fmc-networking/               # Networks, hosts, static routes
│   ├── fmc-network-objects/          # OSPF network objects
│   ├── fmc-policies/                 # Policy assignments
│   ├── fmc-mcd/                      # Multi-Cloud Defense config
│   ├── fmc-ospf/                     # OSPF configuration
│   └── fmc-vpn/                      # VPN site-to-site tunnels
└── scripts/                          # Python automation scripts
    ├── config-import/                # Configuration import utilities
    ├── device-onboarding/            # Device SSH onboarding
    └── ospf/                         # OSPF automation
```

## 🔧 Detailed Module Breakdown

### Core Infrastructure Modules

#### `fmc-devices`
**Purpose**: Device registration and initial configuration import
- Imports pre-built firewall configuration from `.sfo` backup file
- Registers FTD device with CDO/SCC
- Handles device onboarding via SSH automation
- Discovers security zones and policies from imported config

**Key Resources**:
- `cdo_ftd_device`: Device registration
- `null_resource`: Python-based config import and SSH onboarding

#### `fmc-vti-discovery`
**Purpose**: Discovers existing VTI interfaces without managing them
- Data-only module for interface discovery
- Maps logical names to physical tunnel IDs
- Provides interface data for other modules

**Discovered Interfaces**:
- `Tunnel1` → `WAN_static_vti_1`
- `Tunnel2` → `WAN_static_vti_2` 
- `Tunnel3` → `ToSecureAccess`
- `Virtual-Template1` → `WAN_dynamic_vti_1`

#### `fmc-interfaces`
**Purpose**: Configures all physical and VTI interfaces
- 7 physical interfaces (G0/0 through G0/6)
- 4 VTI interfaces (imported via deployment script)
- Security zone assignments
- IP addressing and interface settings

**Interface Layout**:
```
G0/0: WAN (198.18.8.2/24)
G0/1: DMZ (198.18.9.1/24)
G0/2: INTERNET (198.18.3.2/24)
G0/3: DATA-CENTER (198.18.5.1/24)
G0/4: ATTACKER (198.18.14.1/24)
G0/5: Transport (198.18.12.1/24)
G0/6: APP (198.18.11.1/24)
```

#### `fmc-interface-groups`
**Purpose**: Manages interface groupings
- Creates `INSIDE_NETS` group with internal interfaces
- Manages existing `NetFlowGrp` (imported during deployment)

### Network Configuration Modules

#### `fmc-networking`
**Purpose**: Network objects, hosts, and static routing
- Creates branch and overlay networks
- Defines host objects for routing targets
- Configures static routes for reachability

**Key Networks**:
- `Branch-EVPN-Overlay-Main`: 10.10.255.0/24
- `Branch-EVPN-Underlay`: 172.30.255.0/24
- `Coinforge1_net`: 10.104.255.0/24

#### `fmc-network-objects`
**Purpose**: OSPF-specific network objects
- Network objects for OSPF area configuration
- Used by OSPF automation script

**OSPF Networks**:
- `Apps`: 198.18.11.0/24 (data source - pre-existing)
- `Attacker`: 198.18.14.0/24
- `Data-Center`: 198.18.5.0/24
- `DMZ`: 198.18.9.0/24
- `Outside`: 198.18.3.0/24
- `Transport`: 198.18.12.0/24

### Policy and Routing Modules

#### `fmc-policies`
**Purpose**: Policy assignments and platform settings
- Assigns access control policies to devices
- Configures NAT policy assignments
- Applies platform policy settings

#### `fmc-ospf`
**Purpose**: OSPF dynamic routing configuration
- Uses Python automation for API-based OSPF setup
- Configures OSPF Process 1 with Area 0
- Adds all defined networks to OSPF area

**Automation Details**:
- Creates Python virtual environment
- Installs required packages (`requests`)
- Executes `cdfmc_ospf_automation.py` with Terraform-provided parameters
- Uses static domain UUID for cdFMC compatibility

#### `fmc-mcd`
**Purpose**: Multi-Cloud Defense integration
- Creates MCD security zones
- Configures MCD access control policy
- Sets up intrusion policy integration

#### `fmc-vpn`
**Purpose**: Site-to-site VPN tunnels (Always runs last)
- 3 VPN tunnels: AWS1, AWS2, SecureAccess
- IKEv2 configuration with pre-shared keys
- VPN endpoint management

**VPN Tunnels**:
- `AWS_Tunnel_1`: AWS connectivity via Tunnel1
- `AWS_Tunnel_2`: AWS connectivity via Tunnel2  
- `SecureAccessToISE`: ISE integration via Tunnel3

## 🤖 Automation Scripts

### Configuration Import (`scripts/config-import/`)
**Purpose**: Imports pre-built FMC configuration from backup file

**Files**:
- `main.py`: Main import script
- `automation_backup.sfo`: Pre-built configuration backup
- `platsettings.py`: Platform policy configuration

**Usage**: Automatically called by `fmc-devices` module

### Device Onboarding (`scripts/device-onboarding/`)
**Purpose**: SSH-based device onboarding automation

**Files**:
- `cdo.py`: SSH automation for device registration commands

**Usage**: Executes generated onboarding commands on FTD devices

### OSPF Configuration (`scripts/ospf/`)
**Purpose**: API-based OSPF configuration automation

**Files**:
- `cdfmc_ospf_automation.py`: Main OSPF automation script
- `config.py`: Configuration management and parameter updates
- `requirements.txt`: Python dependencies

**Features**:
- Direct REST API calls to cdFMC
- Optimized with minimal API calls
- Configures OSPF Process 1 with Area 0
- Adds networks dynamically based on Terraform data

## 🔄 Deployment Process

### Automated Deployment Script

The `deploy_prep_pod_configuration.sh` script provides intelligent, cached deployment:

1. **Device Registration**: Registers FTD and imports configuration
2. **VTI Discovery**: Maps existing tunnel interfaces
3. **ID Extraction**: Caches interface and device IDs
4. **VTI Import**: Imports VTI interfaces into Terraform state
5. **NetFlow Import**: Manages existing interface groups
6. **Core Configuration**: Applies interfaces, networking, policies
7. **OSPF Configuration**: Sets up dynamic routing
8. **VPN Configuration**: Configures site-to-site tunnels

### Smart Caching Features

- **Progress Tracking**: Skips completed steps on re-runs
- **Resource Detection**: Checks Terraform state before operations
- **ID Caching**: Stores extracted IDs for future runs
- **Fast Recovery**: Quick restart from any failure point

## 🌐 Network Design

### Security Zones
```
WAN: External connectivity
DMZ: Demilitarized zone
INTERNET: Internet access
DATA_CENTER: Internal data center
ATTACKER: Attack simulation
TRANSPORT: OSPF transport
APPS: Application networks
TUNNEL_ZONE: VPN tunnels
SecureAccess: ISE connectivity
DCtoMCD: Multi-cloud defense
```

### Routing Architecture
- **Static Routes**: For AWS and branch connectivity
- **OSPF**: Dynamic routing for internal networks
- **VPN Tunnels**: Site-to-site connectivity

## 🔍 Troubleshooting

### Common Issues

#### Device Onboarding Failures
```bash
# Check device connectivity
ping 198.18.133.30

# Verify SSH access
ssh admin@198.18.133.30

# Review onboarding logs
terraform apply -target=module.fmc_devices
```

#### VTI Interface Import Issues
```bash
# Check discovered interfaces
terraform apply -target=module.fmc_vti_discovery

# Manual interface import
terraform import module.fmc_interfaces.fmc_device_vti_interface.WAN_static_vti_1 "device_id,interface_id"

# Reset cached progress
rm .pod_prepare_progress .vti_ids_cache
```

#### OSPF Configuration Problems
```bash
# Test OSPF script manually
cd scripts/ospf
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 cdfmc_ospf_automation.py --fmc-url 'hostname' --api-key 'token' --device-id 'id' --network-ids '{...}'
```

#### Policy Assignment Failures
```bash
# Verify imported policies exist
terraform plan -target=module.fmc_policies

# Check policy names in tfvars
# Ensure policies match imported configuration
```

### Debug Mode

Enable detailed logging:
```bash
export TF_LOG=DEBUG
terraform apply
```

### State Management

Reset specific modules:
```bash
# Remove problematic resources
terraform state rm module.module_name.resource_name

# Re-import if needed
terraform import module.module_name.resource_name resource_id
```

## 📚 Provider Documentation

- **FMC Provider**: [terraform-provider-fmc](https://registry.terraform.io/providers/CiscoDevNet/fmc/latest/docs)
- **CDO Provider**: [terraform-provider-cdo](https://registry.terraform.io/providers/CiscoDevnet/cdo/latest/docs)
- **FMC API**: [Firepower Management Center REST API Guide](https://developer.cisco.com/docs/fmc-rest-api/)

## 🔒 Security Considerations

### Credential Management
- Store SCC tokens securely
- Use environment variables for sensitive data
- Rotate API tokens regularly

### State File Security
- Store Terraform state securely
- Use remote state backends for team environments
- Encrypt state files

## 🚨 Important Notes

### Execution Order
- **NEVER** change module execution order without understanding dependencies
- **VPN module ALWAYS runs last** to avoid conflicts
- **OSPF runs before VPN** for proper routing setup

### State Management
- VTI interfaces must be imported, not created fresh
- NetFlowGrp interface group is pre-existing and managed
- Some resources require specific import procedures

### API Limitations
- cdFMC has different API behavior than on-premise FMC
- Static domain UUID used for cdFMC compatibility
- Rate limiting may affect large deployments

---

**Version**: 1.0  
**Last Updated**: August 2025  
**Terraform Version**: >= 1.0  
**FMC Provider Version**: 2.0.0-rc4
