variable "resource_group_infrastructure" {
  default = "RG_CLEANAIR_INFRASTRUCTURE"
}
variable "resource_group_datasources" {
  default = "RG_CLEANAIR_DATASOURCES"
}

module "infrastructure" {
  source         = "./infrastructure"
  location       = "${var.infrastructure_location}"
  azure_group_id = "${var.azure_group_id}"
  resource_group = "${var.resource_group_infrastructure}"
  tenant_id      = "${var.tenant_id}"
}

module "datasources" {
  source                        = "./datasources"
  boot_diagnostics_uri          = "${module.infrastructure.boot_diagnostics_uri}"
  keyvault_id                   = "${module.infrastructure.keyvault_id}"
  location                      = "${var.infrastructure_location}"
  resource_group                = "${var.resource_group_datasources}"
  infrastructure_resource_group = "${var.resource_group_infrastructure}"
}
