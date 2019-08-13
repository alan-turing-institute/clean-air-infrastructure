# Setup required providers
provider "azurerm" {
  version = "~>1.24"
}

provider "random" {
  version = "~>2.1"
}

# Create the infrastructure resource group
resource "azurerm_resource_group" "infrastructure" {
  name     = "${var.resource_group}"
  location = "${var.location}"

  tags = {
    environment = "Terraform Clean Air"
  }
}

# Generate a random string that persists for the lifetime of the resource group
resource "random_string" "keyvaultnamesuffix" {
  keepers = {
    resource_group = "${azurerm_resource_group.infrastructure.name}"
  }

  length  = 9
  number  = false
  special = false
  upper   = false
}

# Create the keyvault where passwords are stored
resource "azurerm_key_vault" "cleanair" {
  name                = "kvcleanair-${random_string.keyvaultnamesuffix.result}"
  location            = "${var.location}"
  resource_group_name = "${azurerm_resource_group.infrastructure.name}"
  sku_name            = "standard"
  tenant_id           = "${var.tenant_id}"

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

  tags = {
    environment = "Terraform Clean Air"
  }
}

# Create azure container registry and upload the secrets to travis
resource "azurerm_container_registry" "cleanair" {
  name                     = "CleanAirContainerRegistry"
  resource_group_name      = "${azurerm_resource_group.infrastructure.name}"
  location                 = "${var.location}"
  sku                      = "Basic"
  admin_enabled            = true

  provisioner "local-exec" {
    command = "travis env set ACR_SERVER ${azurerm_container_registry.cleanair.login_server} --private"
  }
  provisioner "local-exec" {
    command = "travis env set ACR_USERNAME ${azurerm_container_registry.cleanair.admin_username} --private"
  }
  provisioner "local-exec" {
    command = "travis env set ACR_PASSWORD ${azurerm_container_registry.cleanair.admin_password} --private"
  }
}

# Write the container registry secrets to file
resource "local_file" "acr_secret" {
    sensitive_content     = "${azurerm_container_registry.cleanair.login_server}\n${azurerm_container_registry.cleanair.admin_username}\n${azurerm_container_registry.cleanair.admin_password}"
    filename = "${path.cwd}/.secrets/.acr_secret.json"
}

# Build the static dataset deployment script
data "template_file" "static_data_docker_template" {
  template = "${file("${path.module}/templates/static_data_docker_insert.template.sh")}"
  vars = {
    acr_login_server = "${azurerm_container_registry.cleanair.login_server}"
    acr_name         = "${azurerm_container_registry.cleanair.name}"
  }
}

resource "local_file" "static_data_docker_file" {
    sensitive_content = "${data.template_file.static_data_docker_template.rendered}"
    filename          = "${path.cwd}/../static_data_local/insert_static_data.sh"
}



