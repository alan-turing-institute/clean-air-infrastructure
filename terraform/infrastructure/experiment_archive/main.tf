# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}

# Create storage account for experiments
# -------------------------------------------
resource "azurerm_storage_account" "this" {
  name                     = "cleanairexperiments"
  resource_group_name      = "${var.resource_group}"
  location                 = "${var.location}"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}
