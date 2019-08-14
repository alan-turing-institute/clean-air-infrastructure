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
  source               = "./inputdata"
  boot_diagnostics_uri = "${module.infrastructure.boot_diagnostics_uri}"
  key_vault_id         = "${module.infrastructure.key_vault_id}"
  registry_server      = "${module.infrastructure.registry_server}"
  resource_group       = "${var.rg_input_data}"
}
