terraform {
  backend "azurerm" {
    storage_account_name = "terraformstorageznmobluw"
    container_name       = "terraformbackend"
    key                  = "terraform.tfstate"
    access_key           = "539AHvNKLDpPktR8ZGISMidwRp3KJ160QvIqvAeLscaFQgKmhIJU7jfpPVb75VNm+zi9mIwZgVM4kN172k/ygA=="
  }
}
