module "infrastructure" {
  source         = "./infrastructure"
  azure_group_id = "${var.azure_group_id}"
  location       = "${var.location}"
  resource_group = "${var.rg_infrastructure}"
  tenant_id      = "${var.tenant_id}"
}

module "databases" {
  source               = "./databases"
  keyvault_id          = "${module.infrastructure.keyvault_id}"
  location             = "${var.location}"
  resource_group       = "${var.rg_databases}"
}

# module "datasources" {
#   source               = "./datasources"
#   keyvault_id          = "${module.infrastructure.keyvault_id}"
#   location             = "${var.infrastructure_location}"
#   resource_group       = "${var.rg_datasources}" "RG_CLEANAIR_DATASOURCES"
#   acr_login_server     = "${module.infrastructure.acr_login_server}"
#   acr_admin_user       = "${module.infrastructure.acr_admin_user}"
#   acr_admin_password   = "${module.infrastructure.acr_admin_password}"
# }
