# Load configuration module
# -------------------------
module "configuration" {
  source = "../configuration"
}

# Ensure the databases resource group exists
# ------------------------------------------
resource "azurerm_resource_group" "this" {
  name     = "${var.resource_group}"
  location = "${module.configuration.location}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases"
  }
}

# Create the inputs database
# --------------------------
module "postgres" {
  source         = "./postgres"
  db_name        = "cleanair-inputs"
  db_size_gb     = 400 #20
  key_vault_id   = "${var.infrastructure.key_vault.id}"
  location       = "${azurerm_resource_group.this.location}"
  resource_group = "${azurerm_resource_group.this.name}"
}
