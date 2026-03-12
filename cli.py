#!/usr/bin/env python3
"""
Pod Management CLI for FMC Lab Environments.

Usage:
    python3 cli.py deploy   — Full pod preparation (device registration, config, VPN)
    python3 cli.py reset    — Clean tenant between student sessions
    python3 cli.py destroy  — Tear down all infrastructure

Self-bootstrapping: creates/reuses scripts/.venv automatically.
"""

# === Self-bootstrap (stdlib only — runs before any third-party imports) ===

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / "scripts" / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python3"
REQUIREMENTS = ROOT_DIR / "scripts" / "requirements.txt"

if not os.environ.get("_CLI_BOOTSTRAPPED"):
    # Ensure venv exists
    if not VENV_DIR.exists():
        print("Creating shared Python virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )
    # Install/update dependencies
    subprocess.run(
        [str(VENV_DIR / "bin" / "pip"), "install", "-q", "-r", str(REQUIREMENTS)],
        check=True,
    )
    # Re-exec with the venv Python
    env = os.environ.copy()
    env["_CLI_BOOTSTRAPPED"] = "1"
    os.execve(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv, env)

# === From here on, we're running inside the venv ===

import json
import re
from typing import Optional

import requests
import typer

# Add project root to sys.path so scripts.lib is importable
sys.path.insert(0, str(ROOT_DIR))

from scripts.lib import terraform as tf
from scripts.lib.console import (
    console,
    print_cached_step,
    print_error,
    print_header,
    print_id_table,
    print_import_status,
    print_step,
    print_success,
    print_summary,
    print_warning,
)
from scripts.lib.tfvars import parse_tfvars

app = typer.Typer(help="Pod management CLI for FMC lab environments.")

PROGRESS_FILE = ROOT_DIR / ".pod_prepare_progress"
CACHE_FILE = ROOT_DIR / ".vti_ids_cache"
DOMAIN_UUID = "e276abec-e0f2-11e3-8169-6d9ed49b625f"
TOTAL_STEPS = 11


# ---------------------------------------------------------------------------
# Progress caching helpers
# ---------------------------------------------------------------------------


def check_step_completed(step_name: str) -> bool:
    """Check if a deploy step was already completed (cached)."""
    if PROGRESS_FILE.exists():
        return step_name in PROGRESS_FILE.read_text().splitlines()
    return False


def mark_step_completed(step_name: str) -> None:
    """Mark a deploy step as completed in the cache file."""
    with PROGRESS_FILE.open("a") as f:
        f.write(f"{step_name}\n")


def load_id_cache() -> dict[str, str]:
    """Load cached IDs from .vti_ids_cache (shell KEY='value' format)."""
    ids: dict[str, str] = {}
    if not CACHE_FILE.exists():
        return ids
    for line in CACHE_FILE.read_text().splitlines():
        match = re.match(r'^(\w+)="(.+)"$', line)
        if match:
            ids[match.group(1)] = match.group(2)
    return ids


def write_id_cache(ids: dict[str, str]) -> None:
    """Write IDs to .vti_ids_cache in shell KEY='value' format."""
    lines = [f'{k}="{v}"' for k, v in ids.items()]
    CACHE_FILE.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Deploy subcommand
# ---------------------------------------------------------------------------


@app.command()
def deploy() -> None:
    """Full pod preparation: device registration, config import, VPN setup."""
    print_header("Pod Preparation Process")

    # Parse credentials
    try:
        tfvars = parse_tfvars(str(ROOT_DIR / "terraform.tfvars"))
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)

    cdfmc_host = tfvars.get("cdfmc_host", "").rstrip("/")
    scc_token = tfvars.get("scc_token", "")

    if not cdfmc_host or not scc_token:
        print_error("cdfmc_host and scc_token must be set in terraform.tfvars.")
        raise typer.Exit(1)

    cwd = str(ROOT_DIR)

    # --- Step 1/11: Terraform Init ---
    step = 1
    print_step(step, TOTAL_STEPS, "Initializing Terraform...")
    with console.status("[step]Running terraform init...[/step]"):
        try:
            tf.init(cwd=cwd)
        except subprocess.CalledProcessError as e:
            print_error(f"terraform init failed:\n{e.stderr}")
            raise typer.Exit(1)
    print_success("Terraform initialized")

    # --- Step 2/11: Python Dependencies ---
    step = 2
    print_step(step, TOTAL_STEPS, "Python dependencies ready")
    # Already handled by self-bootstrap above

    # --- Step 3/11: Device Registration ---
    step = 3
    if check_step_completed("device_registration"):
        print_cached_step(step, TOTAL_STEPS, "Device registration")
    else:
        print_step(step, TOTAL_STEPS, "Registering FTD device...")
        with console.status("[step]Running terraform apply (fmc_devices)...[/step]"):
            try:
                tf.apply(["module.fmc_devices"], cwd=cwd)
            except subprocess.CalledProcessError as e:
                print_error(f"Device registration failed:\n{e.stderr}")
                raise typer.Exit(1)
        mark_step_completed("device_registration")
        print_success("Device registered")

    # --- Step 4/11: VTI Discovery ---
    step = 4
    if check_step_completed("vti_discovery"):
        print_cached_step(step, TOTAL_STEPS, "VTI discovery")
    else:
        print_step(step, TOTAL_STEPS, "Discovering existing VTI interfaces...")
        with console.status(
            "[step]Running terraform apply (fmc_vti_discovery)...[/step]"
        ):
            try:
                tf.apply(["module.fmc_vti_discovery"], cwd=cwd)
            except subprocess.CalledProcessError as e:
                print_error(f"VTI discovery failed:\n{e.stderr}")
                raise typer.Exit(1)
        mark_step_completed("vti_discovery")
        print_success("VTI interfaces discovered")

    # --- Step 5/11: ID Extraction ---
    step = 5
    device_id = ""
    vti1_id = ""
    vti2_id = ""
    netflow_id = ""

    if check_step_completed("id_extraction"):
        print_cached_step(step, TOTAL_STEPS, "ID extraction")
        ids = load_id_cache()
        if not ids:
            print_warning("Cache corrupted, re-extracting IDs...")
            CACHE_FILE.unlink(missing_ok=True)
        else:
            device_id = ids.get("DEVICE_ID", "")
            vti1_id = ids.get("VTI1_ID", "")
            vti2_id = ids.get("VTI2_ID", "")
            netflow_id = ids.get("NETFLOW_ID", "")

    if not device_id:
        print_step(step, TOTAL_STEPS, "Extracting device and interface IDs...")
        with console.status("[step]Refreshing terraform state...[/step]"):
            try:
                tf.refresh(
                    ["module.fmc_devices", "module.fmc_vti_discovery"],
                    cwd=cwd,
                )
            except subprocess.CalledProcessError as e:
                print_error(f"Terraform refresh failed:\n{e.stderr}")
                raise typer.Exit(1)

        # Device ID
        try:
            output = tf.state_show(
                "module.fmc_devices.data.fmc_device.devices[0]",
                cwd=cwd,
            )
            device_id = tf.extract_id_from_state_show(output)
        except subprocess.CalledProcessError:
            device_id = ""

        if not device_id or device_id == "null":
            print_error("Could not get device ID. Device may not be registered yet.")
            raise typer.Exit(1)

        # VTI IDs
        for label, address, setter in [
            (
                "VTI1",
                "module.fmc_vti_discovery.data.fmc_device_vti_interface.WAN_static_vti_1",
                "vti1",
            ),
            (
                "VTI2",
                "module.fmc_vti_discovery.data.fmc_device_vti_interface.WAN_static_vti_2",
                "vti2",
            ),
        ]:
            try:
                output = tf.state_show(address, cwd=cwd)
                val = tf.extract_id_from_state_show(output)
            except subprocess.CalledProcessError:
                val = ""
            if setter == "vti1":
                vti1_id = val
            else:
                vti2_id = val

        # NetFlowGrp ID via FMC API (replaces curl)
        try:
            resp = requests.get(
                f"https://{cdfmc_host}/api/fmc_config/v1/domain/{DOMAIN_UUID}/object/interfacegroups",
                headers={
                    "Authorization": f"Bearer {scc_token}",
                    "Content-Type": "application/json",
                },
                params={"limit": 100},
                verify=False,
                timeout=30,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            grp = [i for i in items if i.get("name") == "NetFlowGrp"]
            netflow_id = grp[0]["id"] if grp else ""
        except Exception:
            netflow_id = ""

        write_id_cache(
            {
                "DEVICE_ID": device_id,
                "VTI1_ID": vti1_id,
                "VTI2_ID": vti2_id,
                "NETFLOW_ID": netflow_id,
            }
        )
        mark_step_completed("id_extraction")

    # Display extracted IDs
    print_id_table(device_id, vti1_id, vti2_id, netflow_id)

    # Validate critical IDs
    if not vti1_id or not vti2_id:
        print_error(
            "VTI IDs could not be determined. "
            "Delete .pod_prepare_progress and .vti_ids_cache and re-run."
        )
        raise typer.Exit(1)

    # --- Step 6/11: VTI Import ---
    step = 6
    print_step(step, TOTAL_STEPS, "Importing VTI interfaces into Terraform state...")

    vti_imports = [
        (
            "module.fmc_interfaces.fmc_device_vti_interface.WAN_static_vti_1",
            vti1_id,
            "WAN Static VTI 1 (Tunnel1)",
        ),
        (
            "module.fmc_interfaces.fmc_device_vti_interface.WAN_static_vti_2",
            vti2_id,
            "WAN Static VTI 2 (Tunnel2)",
        ),
    ]

    for address, vti_id, desc in vti_imports:
        if tf.resource_exists_in_state(address, cwd=cwd):
            print_import_status(desc, already_exists=True)
        else:
            with console.status(f"[step]Importing {desc}...[/step]"):
                try:
                    tf.import_resource(address, f"{device_id},{vti_id}", cwd=cwd)
                except subprocess.CalledProcessError as e:
                    print_error(
                        f"Import failed for {desc} "
                        f"(DEVICE_ID={device_id}, VTI_ID={vti_id})\n{e.stderr}"
                    )
                    raise typer.Exit(1)
            print_import_status(desc, already_exists=False)

    # --- Step 7/11: NetFlowGrp Import ---
    step = 7
    print_step(step, TOTAL_STEPS, "Importing NetFlowGrp interface group...")

    netflow_address = "module.fmc_interface_groups.fmc_interface_group.netflow_managed"
    if tf.resource_exists_in_state(netflow_address, cwd=cwd):
        print_import_status("NetFlowGrp", already_exists=True)
    elif not netflow_id or netflow_id == "null":
        console.print(
            "    [info]NetFlowGrp not found on tenant — will be created by core config[/info]"
        )
    else:
        with console.status("[step]Importing NetFlowGrp...[/step]"):
            try:
                tf.import_resource(netflow_address, netflow_id, cwd=cwd)
            except subprocess.CalledProcessError as e:
                print_error(
                    f"Import failed for NetFlowGrp (ID={netflow_id})\n{e.stderr}"
                )
                raise typer.Exit(1)
        print_import_status("NetFlowGrp", already_exists=False)

    # --- Step 8/11: Core Configuration ---
    step = 8
    if check_step_completed("core_config"):
        print_cached_step(step, TOTAL_STEPS, "Core configuration")
    else:
        print_step(step, TOTAL_STEPS, "Applying core configuration...")
        with console.status(
            "[step]Applying interfaces, networking, objects, groups, policies...[/step]"
        ):
            try:
                tf.apply(
                    [
                        "module.fmc_interfaces",
                        "module.fmc_networking",
                        "module.fmc_network_objects",
                        "module.fmc_interface_groups",
                        "module.fmc_policies",
                    ],
                    refresh=False,
                    cwd=cwd,
                )
            except subprocess.CalledProcessError as e:
                print_error(f"Core configuration failed:\n{e.stderr}")
                raise typer.Exit(1)
        mark_step_completed("core_config")
        print_success("Core configuration applied")

    # --- Step 9/11: OSPF ---
    step = 9
    print_step(step, TOTAL_STEPS, "Applying OSPF configuration...")
    with console.status("[step]Running terraform apply (fmc_ospf)...[/step]"):
        try:
            tf.apply(["module.fmc_ospf"], refresh=False, cwd=cwd)
        except subprocess.CalledProcessError as e:
            print_error(f"OSPF configuration failed:\n{e.stderr}")
            raise typer.Exit(1)
    print_success("OSPF configuration applied")

    # --- Step 10/11: BGP ---
    step = 10
    print_step(step, TOTAL_STEPS, "Applying BGP configuration...")
    with console.status("[step]Running terraform apply (fmc_bgp)...[/step]"):
        try:
            tf.apply(["module.fmc_bgp"], refresh=False, cwd=cwd)
        except subprocess.CalledProcessError as e:
            print_error(f"BGP configuration failed:\n{e.stderr}")
            raise typer.Exit(1)
    print_success("BGP configuration applied")

    # --- Step 11/11: VPN (always last) ---
    step = 11
    print_step(step, TOTAL_STEPS, "Applying VPN configuration (final step)...")
    with console.status("[step]Running terraform apply (fmc_vpn)...[/step]"):
        try:
            tf.apply(["module.fmc_vpn"], refresh=False, cwd=cwd)
        except subprocess.CalledProcessError as e:
            print_error(f"VPN configuration failed:\n{e.stderr}")
            raise typer.Exit(1)
    print_success("VPN configuration applied")

    # --- Cleanup & Summary ---
    PROGRESS_FILE.unlink(missing_ok=True)
    CACHE_FILE.unlink(missing_ok=True)

    print_summary(
        [
            "Device registered",
            "VTI interfaces discovered",
            "VTI interfaces imported into state",
            "NetFlowGrp interface group managed",
            "Security zones attached to VTI interfaces",
            "Networking and network objects configured",
            "Policies configured",
            "OSPF configuration applied",
            "BGP configuration applied",
            "VPN configuration applied (final step)",
            "Full infrastructure deployed",
        ]
    )


# ---------------------------------------------------------------------------
# Reset subcommand
# ---------------------------------------------------------------------------


@app.command()
def reset() -> None:
    """Clean tenant between student sessions so deploy can re-run."""
    print_header("Lab Reset")

    try:
        tfvars = parse_tfvars(str(ROOT_DIR / "terraform.tfvars"))
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)

    scc_token = tfvars.get("scc_token", "")
    scc_host = tfvars.get("scc_host", "")
    cdfmc_host = tfvars.get("cdfmc_host", "").rstrip("/")
    device_name = tfvars.get("device_name", "")

    # Validate required vars
    missing = []
    for name, val in [
        ("scc_token", scc_token),
        ("scc_host", scc_host),
        ("cdfmc_host", cdfmc_host),
        ("device_name", device_name),
    ]:
        if not val:
            missing.append(name)
    if missing:
        print_error("Missing required values in terraform.tfvars:")
        for m in missing:
            console.print(f"    {m}: [error](missing)[/error]")
        raise typer.Exit(1)

    reset_script = ROOT_DIR / "scripts" / "reset" / "reset.py"
    venv_python = str(VENV_PYTHON)

    console.print(f"  Resetting tenant (device: [cyan]{device_name}[/cyan])...")
    with console.status("[step]Running reset script...[/step]"):
        try:
            result = subprocess.run(
                [
                    venv_python,
                    str(reset_script),
                    "--scc-host",
                    scc_host,
                    "--fmc-host",
                    cdfmc_host,
                    "--token",
                    scc_token,
                    "--device-name",
                    device_name,
                ],
                cwd=str(ROOT_DIR / "scripts" / "reset"),
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print_error(f"Reset failed:\n{e.stderr}")
            if e.stdout:
                console.print(e.stdout)
            raise typer.Exit(1)

    if result.stdout:
        console.print(result.stdout.rstrip())

    print_success("Tenant reset complete")
    console.print()


# ---------------------------------------------------------------------------
# Destroy subcommand
# ---------------------------------------------------------------------------


@app.command()
def destroy() -> None:
    """Remove state-only resources and destroy all infrastructure."""
    print_header("Infrastructure Destroy")

    cwd = str(ROOT_DIR)

    # Resources that must be removed from state before destroy
    state_rm_resources = [
        "module.fmc_interface_groups.fmc_interface_group.netflow_managed",
        "module.fmc_network_objects.fmc_network.attacker",
        "module.fmc_network_objects.fmc_network.data_center",
        "module.fmc_network_objects.fmc_network.dmz",
        "module.fmc_network_objects.fmc_network.outside",
        "module.fmc_network_objects.fmc_network.transport",
    ]

    console.print("  Removing pre-existing resources from state...")
    for resource in state_rm_resources:
        short_name = resource.split(".")[-1]
        try:
            tf.state_rm(resource, cwd=cwd)
            print_success(f"Removed {short_name} from state")
        except subprocess.CalledProcessError:
            console.print(f"    [info]  {short_name} — not in state (skipped)[/info]")

    console.print()
    console.print("  [step]Destroying infrastructure...[/step]")
    with console.status("[step]Running terraform destroy...[/step]"):
        try:
            tf.destroy(cwd=cwd)
        except subprocess.CalledProcessError as e:
            print_error(f"Terraform destroy failed:\n{e.stderr}")
            raise typer.Exit(1)

    print_success("All infrastructure destroyed")
    console.print()


# ---------------------------------------------------------------------------
# Suppress urllib3 InsecureRequestWarning for self-signed FMC certs
# ---------------------------------------------------------------------------
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


if __name__ == "__main__":
    app()
if __name__ == "__main__":
    app()
