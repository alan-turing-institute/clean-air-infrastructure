# Load configuration module
module "configuration" {
  source = "../configuration"
}

# Ensure the input data resource group exists
resource "azurerm_resource_group" "input_data" {
  name     = "${var.resource_group}"
  location = "${module.configuration.location}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data"
  }
}

# Set up the necessary networking infrastructure
module "networking" {
  source         = "./networking"
  resource_group = "${azurerm_resource_group.input_data.name}"
}

# Set up a virtual machine to orchestrate the containers
module "container_orchestrator" {
  source                          = "./container_orchestrator"
  boot_diagnostics_uri            = "${var.boot_diagnostics_uri}"
  inputs_db_admin_name_secret     = "${var.inputs_db_admin_name_secret}"
  inputs_db_admin_password_secret = "${var.inputs_db_admin_password_secret}"
  key_vault_id                    = "${var.key_vault_id}"
  key_vault_name                  = "${var.key_vault_name}"
  nsg_id                          = "${module.networking.nsg_id}"
  registry_server                 = "${var.registry_server}"
  resource_group                  = "${azurerm_resource_group.input_data.name}"
  subnet_id                       = "${module.networking.subnet_id}"
}