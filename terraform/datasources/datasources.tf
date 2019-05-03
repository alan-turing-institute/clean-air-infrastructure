# Common network and resource group settings
resource "azurerm_virtual_network" "vnet_cleanair_datasources" {
  name                = "VNET_CLEANAIR_DATASOURCES"
  address_space       = ["10.0.0.0/16"]
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"

  tags {
    environment = "Terraform Clean Air"
  }
}

resource "azurerm_subnet" "subnet_cleanair_datasources" {
  name                 = "SUBNET_CLEANAIR_DATASOURCES"
  resource_group_name  = "${azurerm_resource_group.rg_cleanair_datasources.name}"
  virtual_network_name = "${azurerm_virtual_network.vnet_cleanair_datasources.name}"
  address_prefix       = "10.0.1.0/24"
}

resource "azurerm_network_security_group" "nsg_cleanair_datasources" {
  name                = "NSG_CLEANAIR_DATASOURCES"
  location            = "${var.location}"
  resource_group_name = "${azurerm_resource_group.rg_cleanair_datasources.name}"

  security_rule {
    name                       = "GithubWebhook"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "10.0.1.0/24"
  }

  security_rule {
    name                       = "SSH"
    priority                   = 2000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefixes    = ["193.60.220.240", "193.60.220.253"]
    destination_address_prefix = "*"
  }

  tags {
    environment = "Terraform Clean Air"
  }
}

# Ensure the datasources resource group exists
resource "azurerm_resource_group" "rg_cleanair_datasources" {
  name     = "${var.resource_group}"
  location = "${var.location}"

  tags {
    environment = "Terraform Clean Air"
  }
}

# Build datasources
module "aqn" {
  source               = "./datasource"
  datasource           = "aqn"
  boot_diagnostics_uri = "${var.boot_diagnostics_uri}"
  keyvault_id          = "${var.keyvault_id}"
  location             = "${azurerm_resource_group.rg_cleanair_datasources.location}"
  resource_group       = "${azurerm_resource_group.rg_cleanair_datasources.name}"
  nsg_id               = "${azurerm_network_security_group.nsg_cleanair_datasources.id}"
  subnet_id            = "${azurerm_subnet.subnet_cleanair_datasources.id}"
}

module "laqn" {
  source               = "./datasource"
  datasource           = "laqn"
  boot_diagnostics_uri = "${var.boot_diagnostics_uri}"
  keyvault_id          = "${var.keyvault_id}"
  location             = "${azurerm_resource_group.rg_cleanair_datasources.location}"
  resource_group       = "${azurerm_resource_group.rg_cleanair_datasources.name}"
  nsg_id               = "${azurerm_network_security_group.nsg_cleanair_datasources.id}"
  subnet_id            = "${azurerm_subnet.subnet_cleanair_datasources.id}"
}
