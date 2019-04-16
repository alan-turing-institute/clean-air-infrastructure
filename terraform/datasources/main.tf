# Setup required providers
provider "azurerm" {
  version = "=1.24"
}

# Setup variables
variable "boot_diagnostics_uri" {}
variable "keyvault_id" {}
variable "location" {}
variable "resource_group" {}

