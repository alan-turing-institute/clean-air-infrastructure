module "configuration" {
  source = "./configuration"
}

module "infrastructure" {
  source         = "./infrastructure"
  resource_group = "${var.rg_infrastructure}"
}

module "databases" {
  source         = "./databases"
  key_vault_id   = "${module.infrastructure.key_vault_id}"
  resource_group = "${var.rg_databases}"
}

module "inputdata" {
  source                          = "./inputdata"
  boot_diagnostics_uri            = "${module.infrastructure.boot_diagnostics_uri}"
  inputs_db_admin_name_secret     = "${module.databases.inputs_db_admin_name_secret}"
  inputs_db_admin_password_secret = "${module.databases.inputs_db_admin_password_secret}"
  key_vault_id                    = "${module.infrastructure.key_vault_id}"
  key_vault_name                  = "${module.infrastructure.key_vault_name}"
  registry_server                 = "${module.infrastructure.registry_server}"
  resource_group                  = "${var.rg_input_data}"
}
