output "policy_assignments" {
  description = "Policy assignment resources"
  value = {
    access_policies   = fmc_policy_assignment.access_policy_assignments
    platform_policies = null_resource.platform_policy_assignment
    # nat_policy not present in base tenant being replicated
  }
}
