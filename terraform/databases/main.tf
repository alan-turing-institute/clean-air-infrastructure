# Ensure the databases resource group exists
resource "azurerm_resource_group" "databases" {
  name     = "${var.resource_group}"
  location = "${var.location}"

  tags = {
    environment = "Terraform Clean Air"
  }
}

# Create the inputs database
module "inputs" {
  source               = "./postgres"
  db_name              = "inputs"
  db_size              = 5120
  keyvault_id          = "${var.keyvault_id}"
  location             = "${azurerm_resource_group.databases.location}"
  resource_group       = "${azurerm_resource_group.databases.name}"
}
