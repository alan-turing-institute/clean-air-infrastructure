module "configuration" {
  source         = "./configuration"
}

module "infrastructure" {
  source         = "./infrastructure"
  azure_group_id = "${module.configuration.azure_group_id}"
  location       = "${module.configuration.location}"
  resource_group = "${var.rg_infrastructure}"
  tenant_id      = "${module.configuration.tenant_id}"
}

module "databases" {
  source               = "./databases"
  keyvault_id          = "${module.infrastructure.keyvault_id}"
  location             = "${module.configuration.location}"
  resource_group       = "${var.rg_databases}"
}

module "inputdata" {
  source               = "./inputdata"
  acr_admin_password   = "${module.infrastructure.acr_admin_password}"
  acr_admin_user       = "${module.infrastructure.acr_admin_user}"
  acr_login_server     = "${module.infrastructure.acr_login_server}"
  keyvault_id          = "${module.infrastructure.keyvault_id}"
  location             = "${module.configuration.location}"
  resource_group       = "${var.rg_input_data}"
}
