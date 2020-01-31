# Load configuration module
# -------------------------
module "configuration" {
  source = "../configuration"
}

# Create the infrastructure resource group
# ----------------------------------------
resource "azurerm_resource_group" "this" {
  name     = var.resource_group
  location = module.configuration.location
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}

# Create boot diagnostics storage
# -------------------------------
module "boot_diagnostics" {
  source         = "./boot_diagnostics"
  location       = "${azurerm_resource_group.this.location}"
  resource_group = "${azurerm_resource_group.this.name}"
}

# Create keyvault
# ---------------
module "key_vault" {
  source         = "./key_vault"
  location       = "${azurerm_resource_group.this.location}"
  resource_group = "${azurerm_resource_group.this.name}"
}

# Create container registry
# -------------------------
module "containers" {
  source         = "./containers"
  key_vault      = module.key_vault
  location       = "${azurerm_resource_group.this.location}"
  resource_group = "${azurerm_resource_group.this.name}"
}


