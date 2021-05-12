# Setup required providers
provider "azuread" {
  version = "~>1.1.0"
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