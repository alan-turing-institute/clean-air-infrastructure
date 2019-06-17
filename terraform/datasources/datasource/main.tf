# Setup required providers
provider "azurerm" {
  version = "=1.24"
}

provider "template" {
  version = "=2.1"
}

# Setup variables
variable "datasource" {}
variable "keyvault_id" {}
variable "location" {}

variable "resource_group_db" {}

variable "acr_login_server" {}
variable "acr_admin_user" {}
variable "acr_admin_password" {}

variable "db_size" {}