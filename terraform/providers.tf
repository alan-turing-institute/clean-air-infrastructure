# Setup required providers
provider "azurerm" {
  version = "~>1.24"
}
provider "external" {
  version = "~> 1.2"
}
provider "random" {
  version = "~>2.1"
}
provider "template" {
  version = "~> 2.1"
}