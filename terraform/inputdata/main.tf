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
  source         = "./container_orchestrator"
  databases      = "${var.databases}"
  infrastructure = "${var.infrastructure}"
  machine_name   = "container-orchestrator"
  networking     = module.networking
  resource_group = "${azurerm_resource_group.input_data.name}"
}