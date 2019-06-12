# Create the infrastructure resource group
resource "azurerm_resource_group" "rg_infrastructure" {
  name     = "${var.resource_group}"
  location = "${var.location}"

  tags {
    environment = "Terraform Clean Air"
  }
}

# Generate a random string that persists for the lifetime of the resource group
resource "random_string" "lower_case_letters_keyvaultname" {
  keepers = {
    resource_group = "${azurerm_resource_group.rg_infrastructure.name}"
  }

  length  = 6
  number  = false
  special = false
  upper   = false
}

# Create the keyvault where passwords are stored
resource "azurerm_key_vault" "kvcleanairpasswords" {
  name                = "kvcleanairpass${random_string.lower_case_letters_keyvaultname.result}"
  location            = "${var.location}"
  resource_group_name = "${azurerm_resource_group.rg_infrastructure.name}"
  tenant_id           = "${var.tenant_id}"

  sku {
    name = "standard"
  }

  access_policy {
    tenant_id = "${var.tenant_id}"
    object_id = "${var.azure_group_id}"

    key_permissions = [
      "create",
      "delete",
      "get",
      "list",
    ]

    secret_permissions = [
      "set",
      "delete",
      "get",
      "list",
    ]
  }

  tags {
    environment = "Terraform Clean Air"
  }
}

# Provide outputs which are useful to later Terraform scripts
output "keyvault_id" {
  value = "${azurerm_key_vault.kvcleanairpasswords.id}"
}

# Create azure container registry
resource "azurerm_container_registry" "acr" {
  name                     = "CleanAirContainerRegistry"
  resource_group_name      = "${azurerm_resource_group.rg_infrastructure.name}"
  location                 = "${var.location}"
  sku                      = "Basic"
  admin_enabled            = true

  provisioner "local-exec" {
    command = "travis env set ACR_SERVER ${azurerm_container_registry.acr.login_server} --private"
  }
  provisioner "local-exec" {
    command = "travis env set ACR_USERNAME ${azurerm_container_registry.acr.admin_username} --private"
  }
  provisioner "local-exec" {
    command = "travis env set ACR_PASSWORD ${azurerm_container_registry.acr.admin_password} --private"
  }
}

# Write the container registry secrets to file
resource "local_file" "regcred" {
    sensitive_content     = "${azurerm_container_registry.acr.login_server}\n${azurerm_container_registry.acr.admin_username}\n${azurerm_container_registry.acr.admin_password}"
    filename = "${path.cwd}/.secrets/.regred_secret.json"
}


output "acr_login_server" {
  value = "${azurerm_container_registry.acr.login_server}"
}
output "acr_admin_user" {
  value = "${azurerm_container_registry.acr.admin_username}"
}

output "acr_admin_password" {
  value = "${azurerm_container_registry.acr.admin_password}"
}

