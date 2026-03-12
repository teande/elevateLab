"""Terraform subprocess wrappers for CLI automation."""

import re
import subprocess


def init(cwd: str = ".") -> subprocess.CompletedProcess:
    """Run terraform init."""
    return subprocess.run(
        ["terraform", "init", "-input=false"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def apply(
    targets: list[str],
    auto_approve: bool = True,
    refresh: bool = True,
    cwd: str = ".",
) -> subprocess.CompletedProcess:
    """Run terraform apply with optional -target flags."""
    cmd = ["terraform", "apply"]
    for t in targets:
        cmd.extend(["-target", t])
    if auto_approve:
        cmd.append("-auto-approve")
    if not refresh:
        cmd.append("-refresh=false")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def import_resource(
    address: str,
    resource_id: str,
    cwd: str = ".",
) -> subprocess.CompletedProcess:
    """Run terraform import."""
    return subprocess.run(
        ["terraform", "import", address, resource_id],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def state_show(address: str, cwd: str = ".") -> str:
    """Run terraform state show and return stdout."""
    result = subprocess.run(
        ["terraform", "state", "show", address],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def state_list(cwd: str = ".") -> list[str]:
    """Run terraform state list and return resource addresses."""
    result = subprocess.run(
        ["terraform", "state", "list"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def state_rm(address: str, cwd: str = ".") -> subprocess.CompletedProcess:
    """Run terraform state rm."""
    return subprocess.run(
        ["terraform", "state", "rm", address],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def refresh(targets: list[str], cwd: str = ".") -> subprocess.CompletedProcess:
    """Run terraform refresh with -target flags."""
    cmd = ["terraform", "refresh"]
    for t in targets:
        cmd.extend(["-target", t])
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def destroy(auto_approve: bool = True, cwd: str = ".") -> subprocess.CompletedProcess:
    """Run terraform destroy."""
    cmd = ["terraform", "destroy"]
    if auto_approve:
        cmd.append("-auto-approve")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def resource_exists_in_state(address: str, cwd: str = ".") -> bool:
    """Check if a resource exists in terraform state."""
    try:
        resources = state_list(cwd=cwd)
        return address in resources
    except subprocess.CalledProcessError:
        return False


def extract_id_from_state_show(output: str) -> str:
    """Extract the id value from terraform state show output."""
    match = re.search(r'^\s*id\s*=\s*"([^"]+)"', output, re.MULTILINE)
    return match.group(1) if match else ""
