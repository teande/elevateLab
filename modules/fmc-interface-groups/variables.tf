variable "inside_interfaces" {
  description = "List of interface IDs to add to INSIDE_NETS group"
  type = list(object({
    id = string
  }))
  default = []
}

variable "netflow_interfaces" {
  description = "List of interface IDs to add to NetFlowGrp"
  type = list(object({
    id = string
  }))
  default = null
}
