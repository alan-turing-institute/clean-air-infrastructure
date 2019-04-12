provider "azurerm" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=1.24"
  # subscription_id = "45a2ea24-e10c-4c35-b172-4b956deffbf2"
  subscription_id = "${var.subscription_id}"
}

# Create a resource group
resource "azurerm_resource_group" "cleanair_infrastructure_rg" {
  name     = "${var.resource_group}"
  location = "uksouth"
  tags {
      environment = "Terraform Clean Air"
  }
}

resource "azurerm_storage_account" "cleanair_terraform_backend" {
    name                = "cleanairterraformbackend"
    resource_group_name = "${azurerm_resource_group.cleanair_infrastructure_rg.name}"
    location            = "uksouth"
    account_replication_type = "LRS"
    account_tier = "Standard"

    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_storage_container" "cleanairbackend" {
    name                = "cleanairbackend"
    resource_group_name = "${azurerm_resource_group.cleanair_infrastructure_rg.name}"
    storage_account_name = "${azurerm_storage_account.cleanair_terraform_backend.name}"
    container_access_type = "private"
}