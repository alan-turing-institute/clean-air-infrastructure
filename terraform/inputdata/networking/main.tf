# Set up a virtual network with associated subnet and security group
resource "azurerm_virtual_network" "input_data" {
  name                = "VNET_CLEANAIR_INPUT_DATA"
  address_space       = ["10.10.0.0/16"]
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Networking"
  }
}
resource "azurerm_subnet" "input_data" {
  name                 = "SUBNET_CLEANAIR_INPUT_DATA"
  resource_group_name  = "${azurerm_virtual_network.input_data.resource_group_name}"
  virtual_network_name = "${azurerm_virtual_network.input_data.name}"
  address_prefix       = "10.10.0.0/24"
}
resource "azurerm_network_security_group" "input_data" {
  name                = "NSG_CLEANAIR_INPUT_DATA"
  location            = "${azurerm_virtual_network.input_data.location}"
  resource_group_name = "${azurerm_virtual_network.input_data.resource_group_name}"

  security_rule {
    name                       = "GithubWebhook"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "10.10.0.0/24"
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
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Networking"
  }
}