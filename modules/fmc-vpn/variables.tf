variable "devices" {
  description = "FMC devices"
  type        = list(object({
    id = string
  }))
}

variable "vti_interfaces" {
  description = "VTI interfaces"
  type = object({
    vti_1 = object({
      id = string
    })
    vti_2 = object({
      id = string
    })
  })
}
