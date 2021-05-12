# Setup required providers
provider "azuread" {
  version = "~>0.7"
}
provider "azurerm" {
  version = "~>2.31.0"
  features {}
}
provider "external" {
  version = "~> 1.2"
}
provider "random" {
  version = "~>2.2"
}
provider "template" {
  version = "~> 2.1.2"
}