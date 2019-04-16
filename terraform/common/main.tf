# Setup variables
variable "location" {}
variable "object_id" {}
variable "resource_group" {}
variable "tenant_id" {}

# Setup required providers
provider "azurerm" {
  version = "=1.24"
}

provider "random" {
  version = "=2.1"
}

# Create the Clean Air resource group
resource "azurerm_resource_group" "rg_infrastructure" {
  name     = "${var.resource_group}"
  location = "${var.location}"
  tags {
      environment = "Terraform Clean Air"
  }
}

# resource "random_id" "randomId" {
#     keepers = {
#         # Generate a new ID whenever a new resource group is defined
#         resource_group = "${var.resource_group}"
#     }
#     byte_length = 8
# }

# resource "azurerm_storage_account" "cleanair_storageaccount" {
#     name                     = "${random_id.randomId.hex}"
#     resource_group_name      = "${var.resource_group}"
#     location                 = "${var.location}"
#     account_replication_type = "LRS"
#     account_tier             = "Standard"
#     tags {
#         environment = "Terraform Clean Air"
#     }
# }

# # resource "azurerm_storage_container" "clean_air_terraform_backend" {
# #   name                  = "terraform-backend"
# #   resource_group_name   = "${var.resource_group}"
# #   storage_account_name  = "${azurerm_storage_account.cleanair_storageaccount.name}"
# #   container_access_type = "private"
# # }

# # resource "azurerm_storage_blob" "clean_air_terraform_backend_blob" {
# #   name = "terraform-backend-blob"

# #   resource_group_name    = "${var.resource_group}"
# #   storage_account_name   = "${azurerm_storage_account.cleanair_storageaccount.name}"
# #   storage_container_name = "${azurerm_storage_container.clean_air_terraform_backend.name}"

# #   type = "page"
# #   size = 5120
# # }

# resource "random_string" "password" {
#   length = 16
#   special = true
#   # override_special = "/@\" "
# }

resource "azurerm_key_vault" "kvcleanairpasswords" {
  name                = "kvcleanairpasswords"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  tenant_id           = "${var.tenant_id}"
  sku {
    name = "standard"
  }

  access_policy {
    tenant_id          = "${var.tenant_id}"
    object_id          = "${var.object_id}"
    key_permissions    = [
      "create",
      "delete",
      "get",
      "list"
    ]
    secret_permissions = [
      "set",
      "delete",
      "get",
      "list"
    ]
  }
}

data "azurerm_client_config" "current" {}
output "keyvault_id" {
    value = "${azurerm_key_vault.kvcleanairpasswords.id}"
}



# resource "azurerm_key_vault_secret" "cleanair_LAQN_set_password" {
#   name         = "laqn-admin-password"
#   value        = "${random_string.password.result}"
#   key_vault_id = "${azurerm_key_vault.kvpasswords.id}"
# }