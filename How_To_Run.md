# How to Run — Elevate Lab

> **Note:** Your lab session folder may contain a `challenge-Lab` directory for a different lab exercise.
> This guide covers the **Elevate Lab** — a separate project found in the `elevateLab` folder.
> Do not mix up the two.

---

## First Time: Clone the Repository

```bash
git clone <repo-url> elevateLab
cd elevateLab
```

## Already Have It: Pull Latest Changes

```bash
cd elevateLab
git pull
```

---

## Step 1 — Configure Your Credentials

Fill in your tenant credentials:

```bash
nano terraform.tfvars
```

Edit `terraform.tfvars`: To paste the copied token or url into the webrdp sessions, use the "right-click" on mouse.

```hcl
scc_token  = "your-scc-api-token"
scc_host   = "https://eu.manage.security.cisco.com"   # or us/apj — match your region
cdfmc_host = "your-cdfmc-hostname.cisco.com"          # no https://

# Pre-configured for the lab environment — do not change unless instructed
ftd_ips     = ["198.18.133.39"]
device_name = ["hqftdv"]
policies    = ["HQ Firewall Policy"]
```

Your `scc_token` and `scc_host` come from the CDO/SCC portal. Ask your instructor if you don't have them.

> `terraform.tfvars` is gitignored — it will never be committed to the repo.

---

## Step 2 — Deploy the Lab

```bash
./cli.py deploy
```

This runs the full automated deployment. It will:

1. Initialize Terraform providers
2. Register the FTD device with CDO
3. Import the base firewall configuration from the `.sfo` backup
4. Configure all interfaces, routes, security zones, and policy assignments
5. Apply OSPF, BGP, and VPN configurations

**The first run takes approximately 10–15 minutes** due to device registration and configuration sync waits.

If the deploy stops partway through, just run it again — completed steps are cached and will be skipped.

---

## Step 3 — Reset Between Sessions

Once the student is done with the pod (or you need to start fresh), run:

```bash
./cli.py reset
```

This cleans the cdFMC tenant and clears Terraform state so the next deploy starts from a known-good state. It:

1. Deletes the S2S VPN topology
2. Deregisters the FTD from CDO
3. Deletes the Access Control Policy (re-created on next deploy)
4. Clears all device-specific Terraform state
5. Clears the deploy cache

After reset, run `./cli.py deploy` as normal.

---

## Quick Reference

| Task                   | Command                                                         |
| ---------------------- | --------------------------------------------------------------- |
| First-time setup       | `git clone <repo-url> elevateLab && cd elevateLab`              |
| Get latest code        | `git pull`                                                      |
| Deploy lab             | `./cli.py deploy`                                               |
| Reset for next session | `./cli.py reset`                                                |
| Full teardown          | `./cli.py destroy`                                              |
| Force re-run deploy    | `rm -f .pod_prepare_progress .vti_ids_cache && ./cli.py deploy` |

---

## Troubleshooting

**`terraform.tfvars` not found**
You need to create it — see Step 1 above.

**Deploy fails at device registration**
Check that `ftd_ips` in `terraform.tfvars` matches the FTD IP for your pod. Verify SSH access to the device.

**Deploy fails with "ACP not found"**
The Access Control Policy wasn't imported. Run `./cli.py reset` to clear state, then re-deploy.

**Deploy fails mid-way**
Just re-run `./cli.py deploy`. Completed steps are cached and skipped automatically.

**Need to force everything to re-run**
```bash
rm -f .pod_prepare_progress .vti_ids_cache
./cli.py deploy
```

**Enable debug logging**
```bash
export TF_LOG=DEBUG
terraform apply
```
