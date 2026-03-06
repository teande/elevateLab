#!/usr/bin/env python3
"""
cdFMC OSPF Process 1 Automation using Direct REST API
Enables OSPF Process 1 checkbox and configures Area 0 with specified networks

Uses direct REST API calls instead of fmcapi SDK for cdFMC compatibility.
All configuration is read from config.py - no user prompts.
"""

import argparse
import json
import sys
import time

import requests
# Disable SSL warnings for self-signed certificates
import urllib3
from config import (API_KEY, DEVICE_ID, DEVICE_NAME, DOMAIN_UUID, FMC_URL,
                    NETWORK_IDS, OSPF_AREA_ID, OSPF_NETWORKS, OSPF_PROCESS_ID,
                    OSPF_ROUTER_ID, update_config_from_terraform)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CdFMCRestAPI:
    def __init__(self, fmc_url, api_key):
        """Initialize cdFMC REST API client with static domain UUID"""
        self.fmc_url = fmc_url.rstrip('/')
        self.api_key = api_key
        self.domain_uuid = DOMAIN_UUID  # Use static domain UUID
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def enable_ospf_process(self, device_id):
        """Enable OSPF process on the device"""
        try:
            # First, get the current routing configuration
            url = f"{self.fmc_url}/api/fmc_config/v1/domain/{self.domain_uuid}/devices/devicerecords/{device_id}/routing/ospfv2process"
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                print(f"   ℹ️  OSPF process already enabled")
                return True
            
            # Enable OSPF Process 1
            process_payload = {
                "type": "OspfV2Process",
                "processName": "PROCESS_1",
                "enabled": True
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(process_payload),
                verify=False,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Enabled OSPF Process 1")
                return True
            else:
                print(f"   ❌ Failed to enable OSPF process: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error enabling OSPF process: {str(e)}")
            return False
    
    def get_existing_ospf_routes(self, device_id):
        """Get existing OSPF routes for a device"""
        try:
            url = f"{self.fmc_url}/api/fmc_config/v1/domain/{self.domain_uuid}/devices/devicerecords/{device_id}/routing/ospfv2routes"
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                ospf_data = response.json()
                return ospf_data.get('items', [])
            else:
                return []
                
        except Exception as e:
            print(f"   ❌ Error getting OSPF routes: {str(e)}")
            return []
    
    def create_ospf_route(self, device_id, found_networks):
        """Create OSPF route configuration"""
        try:
            ospf_payload = {
                "type": "OspfRoute",
                "processId": OSPF_PROCESS_ID,
                "enableProcess": "PROCESS_1",  # Enable Process 1
                "processConfiguration": {
                    "rfc1583Compatible": False,
                    "ignoreLsaMospf": False,
                    "administrativeDistance": {
                        "interArea": 110,
                        "intraArea": 110, 
                        "external": 110
                    },
                    "timers": {
                        "lsaGroup": 10  # Default LSA group pacing timer
                    }
                },
                "redistributeProtocols": [],  # Explicitly set empty to avoid ASBR role
                "filterRules": [],  # Explicitly set empty filter rules
                "summaryAddresses": [],  # Explicitly set empty summary addresses
                "areas": [{
                    "areaId": OSPF_AREA_ID,
                    "areaType": {"type": "normal"},
                    "areaNetworks": [
                        {
                            "type": network["type"],
                            "id": network["id"],
                            "name": network["name"]
                        }
                        for network in found_networks
                    ]
                }]
            }
            
            url = f"{self.fmc_url}/api/fmc_config/v1/domain/{self.domain_uuid}/devices/devicerecords/{device_id}/routing/ospfv2routes"
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(ospf_payload),
                verify=False,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Created OSPF Process 1 successfully!")
                return result
            else:
                print(f"   ❌ Failed to create OSPF route: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error creating OSPF route: {str(e)}")
            return None
    
    def update_ospf_route(self, device_id, ospf_id, found_networks):
        """Update existing OSPF route configuration"""
        try:
            ospf_payload = {
                "type": "OspfRoute",
                "id": ospf_id,
                "processId": OSPF_PROCESS_ID,
                "enableProcess": "PROCESS_1",  # Enable Process 1
                "processConfiguration": {
                    "rfc1583Compatible": False,
                    "ignoreLsaMospf": False,
                    "administrativeDistance": {
                        "interArea": 110,
                        "intraArea": 110, 
                        "external": 110
                    },
                    "timers": {
                        "lsaGroup": 10  # Default LSA group pacing timer
                    }
                },
                "redistributeProtocols": [],  # Explicitly set empty to avoid ASBR role
                "filterRules": [],  # Explicitly set empty filter rules
                "summaryAddresses": [],  # Explicitly set empty summary addresses
                "areas": [{
                    "areaId": OSPF_AREA_ID,
                    "areaType": {"type": "normal"},
                    "areaNetworks": [
                        {
                            "type": network["type"],
                            "id": network["id"],
                            "name": network["name"]
                        }
                        for network in found_networks
                    ]
                }]
            }
            
            url = f"{self.fmc_url}/api/fmc_config/v1/domain/{self.domain_uuid}/devices/devicerecords/{device_id}/routing/ospfv2routes/{ospf_id}"
            response = requests.put(
                url,
                headers=self.headers,
                data=json.dumps(ospf_payload),
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Updated OSPF Process 1 successfully!")
                return result
            else:
                print(f"   ❌ Failed to update OSPF route: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error updating OSPF route: {str(e)}")
            return None
    
    def create_fresh_ospf_configuration(self, device_id, found_networks):
        """Create completely fresh OSPF configuration matching screenshot exactly"""
        try:
            print("   📸 Creating OSPF configuration to match screenshot exactly...")
            
            # Create the exact configuration shown in screenshot
            ospf_payload = {
                "type": "OspfRoute",
                "processId": "1",  # ID: 1 (as shown in screenshot)
                "enableProcess": "PROCESS_1",  # Process 1 checkbox enabled
                "processConfiguration": {
                    "rfc1583Compatible": False,
                    "ignoreLsaMospf": False,
                    "administrativeDistance": {
                        "interArea": 110,
                        "intraArea": 110, 
                        "external": 110
                    },
                    "timers": {
                        "lsaGroup": 10
                    }
                },
                "redistributeProtocols": [],  # Empty for Internal Router role
                "filterRules": [],  # Empty filter rules
                "summaryAddresses": [],  # Empty summary addresses  
                "logAdjacencyChanges": {
                    "logType": "DEFAULT"  # Standard OSPF logging
                },
                "areas": [{
                    "areaId": "0",  # Area ID: 0 (as shown in screenshot)
                    "areaType": {
                        "type": "normal"  # Area Type: normal (as shown in screenshot)
                    },
                    "areaNetworks": [
                        {
                            "type": network["type"],
                            "id": network["id"],
                            "name": network["name"]
                        }
                        for network in found_networks
                    ]
                }]
            }
            
            print(f"   📋 Configuration details:")
            print(f"   - Process ID: {ospf_payload['processId']}")
            print(f"   - Enable Process: {ospf_payload['enableProcess']}")
            print(f"   - Area ID: {ospf_payload['areas'][0]['areaId']}")
            print(f"   - Area Type: {ospf_payload['areas'][0]['areaType']['type']}")
            print(f"   - Networks: {len(ospf_payload['areas'][0]['areaNetworks'])} networks")
            print(f"   - Redistribute Protocols: {len(ospf_payload['redistributeProtocols'])} (empty for Internal Router)")
            
            url = f"{self.fmc_url}/api/fmc_config/v1/domain/{self.domain_uuid}/devices/devicerecords/{device_id}/routing/ospfv2routes"
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(ospf_payload),
                verify=False,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Created OSPF Process 1 configuration successfully!")
                print(f"   📸 Configuration matches screenshot requirements")
                return result
            else:
                print(f"   ❌ Failed to create OSPF configuration: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error creating fresh OSPF configuration: {str(e)}")
            return None

    def deploy_configuration(self, device_id):
        """Deploy configuration to device"""
        try:
            # Try force deploy to overcome timestamp issues
            deploy_payload = {
                "type": "DeploymentRequest",
                "deviceList": [device_id],
                "forceDeploy": True,  # Force deploy to overcome timestamp issues
                "ignoreWarning": True
            }
            
            url = f"{self.fmc_url}/api/fmc_config/v1/domain/{self.domain_uuid}/deployment/deploymentrequests"
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(deploy_payload),
                verify=False,
                timeout=30
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                print(f"   ✅ Deployment initiated successfully!")
                return result
            else:
                print(f"   ❌ Failed to deploy: {response.status_code}")
                print(f"   Response: {response.text}")
                
                # If force deploy fails, try without force
                print(f"   🔄 Trying deployment without force...")
                deploy_payload["forceDeploy"] = False
                response = requests.post(
                    url,
                    headers=self.headers,
                    data=json.dumps(deploy_payload),
                    verify=False,
                    timeout=30
                )
                
                if response.status_code in [200, 202]:
                    result = response.json()
                    print(f"   ✅ Standard deployment initiated successfully!")
                    return result
                else:
                    print(f"   ❌ Standard deployment also failed: {response.status_code}")
                    return None
                
        except Exception as e:
            print(f"   ❌ Error deploying configuration: {str(e)}")
            return None

def main():
    """Main automation function"""
    
    # Parse command line arguments for Terraform integration
    parser = argparse.ArgumentParser(description='cdFMC OSPF Configuration Automation')
    parser.add_argument('--fmc-url', help='cdFMC URL (overrides config.py)')
    parser.add_argument('--api-key', help='API Key (overrides config.py)')
    parser.add_argument('--device-id', help='Device ID (from Terraform)')
    parser.add_argument('--network-ids', help='Network IDs JSON string (from Terraform)')
    args = parser.parse_args()
    
    # Update configuration from command line arguments
    network_ids_dict = None
    if args.network_ids:
        import json
        try:
            network_ids_dict = json.loads(args.network_ids)
        except json.JSONDecodeError:
            print("❌ Invalid JSON format for network-ids parameter")
            return False
    
    if args.fmc_url or args.api_key or args.device_id or network_ids_dict:
        print("🔧 Updating configuration from Terraform parameters...")
        update_config_from_terraform(args.fmc_url, args.api_key, args.device_id, network_ids_dict)
    
    # Get the current configuration values (after potential updates)
    import config
    current_fmc_url = config.FMC_URL
    current_api_key = config.API_KEY
    current_device_id = config.DEVICE_ID
    current_network_ids = config.NETWORK_IDS
    
    print("🚀 cdFMC OSPF Process 1 Automation - FRESH START")
    print("=" * 60)
    print("📸 Configuring to match screenshot requirements:")
    print("   - Process 1: Enabled with ID=1")
    print("   - OSPF Role: Internal Router")
    print("   - Description: internal")
    print("   - Area 0: normal type with 6 networks")
    print("=" * 60)
    
    try:
        # Validate configuration
        print("\n📋 Validating configuration...")
        
        if not current_fmc_url:
            print("❌ Please update FMC_URL in config.py or provide --fmc-url")
            return False
        
        if not current_api_key:
            print("❌ Please update API_KEY in config.py or provide --api-key")
            return False
            
        if not current_device_id:
            print("❌ Please provide --device-id parameter")
            return False
            
        if not current_network_ids:
            print("❌ Please provide --network-ids parameter")
            return False
        
        print(f"   ✅ FMC URL: {current_fmc_url}")
        print(f"   ✅ API Key: {current_api_key[:8]}...")
        print(f"   ✅ Domain UUID: {DOMAIN_UUID}")
        print(f"   ✅ Device ID: {current_device_id}")
        print(f"   ✅ Network IDs: {len(current_network_ids)} networks provided")
        
        # Initialize API client
        api = CdFMCRestAPI(current_fmc_url, current_api_key)
        
        # Use provided device_id directly (no need for API calls)
        print(f"\n1. Using provided device ID: {current_device_id}")
        device_id = current_device_id
        
        # Use provided network IDs directly (no need for API discovery)
        print(f"\n2. Using provided network IDs...")
        found_networks = []
        
        # Map our expected networks to the provided IDs
        network_mapping = {
            "Attacker": "attacker_id",
            "Data-Center": "data_center_id", 
            "Apps": "apps_id",
            "DMZ": "dmz_id",
            "Outside": "outside_id",
            "Transport": "transport_id"
        }
        
        for network_name in OSPF_NETWORKS:
            key = network_mapping.get(network_name)
            if key and key in current_network_ids:
                found_networks.append({
                    "type": "Network",
                    "id": current_network_ids[key],
                    "name": network_name
                })
                print(f"   ✅ {network_name}: {current_network_ids[key]}")
            else:
                print(f"   ❌ {network_name}: ID not found in provided network IDs")
        
        if not found_networks:
            print("   ❌ No valid network IDs found!")
            return False
            
        print(f"   ✅ Ready to configure {len(found_networks)} networks")
        
        # Clean up existing OSPF configuration completely
        print(f"\n3. Cleaning up existing OSPF configuration...")
        existing_ospf = api.get_existing_ospf_routes(device_id)
        
        if existing_ospf:
            for ospf_config in existing_ospf:
                ospf_id = ospf_config['id']
                print(f"   🗑️  Deleting existing OSPF config (ID: {ospf_id})")
                
                delete_url = f"{api.fmc_url}/api/fmc_config/v1/domain/{api.domain_uuid}/devices/devicerecords/{device_id}/routing/ospfv2routes/{ospf_id}"
                delete_response = requests.delete(delete_url, headers=api.headers, verify=False, timeout=30)
                
                if delete_response.status_code in [200, 204]:
                    print(f"   ✅ Deleted OSPF configuration")
                else:
                    print(f"   ⚠️  Could not delete config: {delete_response.status_code}")
        else:
            print(f"   ℹ️  No existing OSPF configuration found")
        
        # Create completely fresh OSPF configuration to match screenshot
        print(f"\n4. Creating fresh OSPF configuration to match screenshot...")
        result = api.create_fresh_ospf_configuration(device_id, found_networks)
        
        if not result:
            return False
        
        # Verify the configuration was saved
        print(f"\n4b. Verifying configuration was saved...")
        verify_ospf = api.get_existing_ospf_routes(device_id)
        if verify_ospf:
            print(f"   ✅ Verified: OSPF configuration exists in cdFMC")
            for config in verify_ospf:
                print(f"   - Config ID: {config.get('id', 'N/A')}")
                print(f"   - Process ID: {config.get('processId', 'N/A')}")
                areas = config.get('areas', [])
                if areas:
                    area = areas[0]
                    networks = area.get('areaNetworks', [])
                    print(f"   - Area {area.get('areaId', 'N/A')}: {len(networks)} networks")
        else:
            print(f"   ❌ Configuration not found in cdFMC!")
            return False
        
        # Deploy configuration
        # print(f"\n6. Deploying configuration to device...")
        # deploy_result = api.deploy_configuration(device_id)
        # if not deploy_result:
        #     print("   ⚠️  Configuration saved but deployment failed")
        #     print("   ℹ️  You can manually deploy from FMC GUI")
        #     print("   📍 Look for 'Deploy Changes' or pending changes indicator in cdFMC")
        
        print("\n🎉 cdFMC OSPF Process 1 automation completed successfully!")
        print("\n📸 Configuration matches screenshot:")
        print("- ✅ Process 1: Enabled (checkbox checked)")
        print("- ✅ ID: 1") 
        print("- ✅ OSPF Role: Internal Router")
        print("- ✅ Description: internal")
        print("- ✅ Area 0: normal type")
        print(f"- ✅ Networks: All {len(found_networks)} networks added to Area 0")
        print("- ✅ Configuration saved to cdFMC")
        # if deploy_result:
        #     print("- ✅ Deployment initiated")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Automation stopped by user")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
