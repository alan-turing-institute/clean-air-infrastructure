variable "resource_group_infrastructure" {
  default = "RG_CLEANAIR_INFRASTRUCTURE"
}

variable "resource_group_datasources" {
  default = "RG_CLEANAIR_DATASOURCES"
}

variable "resource_group_databases" {
  default = "RG_CLEANAIR_DATABASES"
}

module "infrastructure" {
  source         = "./infrastructure"
  location       = "${var.infrastructure_location}"
  azure_group_id = "${var.azure_group_id}"
  resource_group = "${var.resource_group_infrastructure}"
  tenant_id      = "${var.tenant_id}"
}

module "datasources" {
  source               = "./datasources"
  boot_diagnostics_uri = "${module.infrastructure.boot_diagnostics_uri}"
  keyvault_id          = "${module.infrastructure.keyvault_id}"
  location             = "${var.infrastructure_location}"
  resource_group       = "${var.resource_group_datasources}"
  resource_group_db    = "${var.resource_group_databases}"
  acr_login_server     = "${module.infrastructure.acr_login_server}"
  acr_admin_user       = "${module.infrastructure.acr_admin_user}"
  acr_admin_password   = "${module.infrastructure.acr_admin_password}"
}
