# Ensure the input data resource group exists
resource "azurerm_resource_group" "input_data" {
  name     = "${var.resource_group}"
  location = "${var.location}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data"
  }
}

# Set up the necessary networking infrastructure
module "networking" {
  source               = "./networking"
  location             = "${azurerm_resource_group.input_data.location}"
  resource_group       = "${azurerm_resource_group.input_data.name}"
}

# Set up a virtual machine to orchestrate the containers
module "container_orchestrator" {
  source               = "./container_orchestrator"
  acr_admin_password   = "${var.acr_admin_password}"
  acr_admin_user       = "${var.acr_admin_user}"
  acr_login_server     = "${var.acr_login_server}"
  keyvault_id          = "${var.keyvault_id}"
  location             = "${azurerm_resource_group.input_data.location}"
  nsg_id               = "${module.networking.nsg_id}"
  resource_group       = "${azurerm_resource_group.input_data.name}"
  subnet_id            = "${module.networking.subnet_id}"
}
