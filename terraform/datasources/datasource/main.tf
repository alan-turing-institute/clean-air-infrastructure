# Setup required providers
provider "azurerm" {
  version = "=1.24"
}
provider "template" {
  version = "=2.1"
}

# Setup variables
variable "boot_diagnostics_uri" {}
variable "cloud_init_merge" {
  default     = "list(append)+dict(recurse_array)+str()"
  description = "Control how cloud-init merges user-data sections"
}
variable "datasource" {}
variable "keyvault_id" {}
variable "location" {}
variable "nsg_id" {}
variable "resource_group" {}
variable "subnet_id" {}