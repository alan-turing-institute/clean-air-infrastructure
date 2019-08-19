module "configuration" {
  source = "./configuration"
}

module "infrastructure" {
  source         = "./infrastructure"
  resource_group = "${var.rg_infrastructure}"
}

module "databases" {
  source         = "./databases"
  infrastructure = module.infrastructure
  resource_group = "${var.rg_databases}"
}

module "inputdata" {
  source         = "./inputdata"
  databases      = module.databases
  infrastructure = module.infrastructure
  resource_group = "${var.rg_input_data}"
}
