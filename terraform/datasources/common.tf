# Ensure the datasources resource group exists
resource "azurerm_resource_group" "rg_cleanair_datasources" {
  name     = "${var.resource_group}"
  location = "${var.location}"
  tags {
      environment = "Terraform Clean Air"
  }
}

resource "azurerm_virtual_network" "vnet_cleanair_datasources" {
    name                = "VNET_CLEANAIR_DATASOURCES"
    address_space       = ["10.0.0.0/16"]
    location            = "${var.location}"
    resource_group_name = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_subnet" "subnet_cleanair_datasources" {
    name                 = "SUBNET_CLEANAIR_DATASOURCES"
    resource_group_name  = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    virtual_network_name = "${azurerm_virtual_network.vnet_cleanair_datasources.name}"
    address_prefix       = "10.0.2.0/24"
}

resource "azurerm_network_security_group" "nsg_cleanair_datasources" {
    name                = "NSG_CLEANAIR_DATASOURCES"
    location            = "${var.location}"
    resource_group_name = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    security_rule {
        name                       = "SSH"
        priority                   = 1001
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "22"
        source_address_prefix      = "193.60.220.240"
        destination_address_prefix = "*"
    }
    tags {
        environment = "Terraform Clean Air"
    }
}