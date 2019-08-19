module "configuration" {
  source = "./configuration"
}

module "infrastructure" {
  source         = "./infrastructure"
  resource_group = "${var.resource_group_infrastructure}"
}

module "databases" {
  source         = "./databases"
  infrastructure = module.infrastructure
  resource_group = "${var.resource_group_databases}"
}

module "data_collection" {
  source         = "./data_collection"
  databases      = module.databases
  infrastructure = module.infrastructure
  resource_group = "${var.resource_group_data_collection}"
}
