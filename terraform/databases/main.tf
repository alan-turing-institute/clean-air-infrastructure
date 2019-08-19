# Load configuration module
module "configuration" {
  source = "../configuration"
}

# Ensure the databases resource group exists
resource "azurerm_resource_group" "this" {
  name     = "${var.resource_group}"
  location = "${module.configuration.location}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases"
  }
}

# Create the inputs database
module "inputs" {
  source         = "./postgres"
  db_name        = "inputs"
  db_size        = 5120
  key_vault_id   = "${var.key_vault_id}"
  location       = "${azurerm_resource_group.this.location}"
  resource_group = "${azurerm_resource_group.this.name}"
}

