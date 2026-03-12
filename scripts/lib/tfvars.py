"""Parse terraform.tfvars files."""

import re
from pathlib import Path


def parse_tfvars(path: str = "terraform.tfvars") -> dict[str, str]:
    """Parse terraform.tfvars and return a dict of key -> value.

    Handles both formats:
      key = "value"
      key = ["value1", "value2"]   (returns first value)
    """
    tfvars_path = Path(path)
    if not tfvars_path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy terraform.tfvars.ignore and populate credentials."
        )

    variables: dict[str, str] = {}
    content = tfvars_path.read_text()

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match: key = "value" or key = ["value1", "value2"]
        match = re.match(r"^(\w+)\s*=\s*(.+)$", line)
        if not match:
            continue

        key = match.group(1)
        raw_value = match.group(2).strip()

        # Strip brackets, split on comma, take first, strip quotes
        raw_value = raw_value.strip("[]")
        first_value = raw_value.split(",")[0].strip().strip('"').strip("'")
        variables[key] = first_value

    return variables
