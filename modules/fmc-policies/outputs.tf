output "policy_assignments" {
  description = "Policy assignment resources"
  value = {
    access_policies = fmc_policy_assignment.access_policy_assignments
    nat_policy = fmc_policy_assignment.dc_nat_policy
    platform_policies = null_resource.platform_policy_assignment
  }
}
