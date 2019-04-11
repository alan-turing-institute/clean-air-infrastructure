provider "azurerm" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=1.24"
  subscription_id = "45a2ea24-e10c-4c35-b172-4b956deffbf2"
}

resource "azurerm_resource_group" "myterraformgroup" {
  name     = "RG_CLEAN_AIR_INFRASTRUCTURE"
  location = "uksouth"
  tags {
      environment = "Terraform Clean Air"
  }
}