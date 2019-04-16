# Setup variables
variable "location" {}
variable "resource_group" {}
variable "keyvault_id" {}

# Setup required providers
provider "azurerm" {
  version = "=1.24"
}

provider "random" {
  version = "=2.1"
}

# Ensure the datasources resource group exists
resource "azurerm_resource_group" "rg_datasources" {
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
    resource_group_name = "${azurerm_resource_group.rg_datasources.name}"
    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_subnet" "subnet_cleanair_datasources" {
    name                 = "SUBNET_CLEANAIR_DATASOURCES"
    resource_group_name  = "${azurerm_resource_group.rg_datasources.name}"
    virtual_network_name = "${azurerm_virtual_network.vnet_cleanair_datasources.name}"
    address_prefix       = "10.0.2.0/24"
    tags {
        environment = "Terraform Clean Air"
    }
}


resource "azurerm_network_security_group" "nsg_cleanair_datasources" {
    name                = "NSG_CLEANAIR_DATASOURCES"
    location            = "${var.location}"
    resource_group_name = "${azurerm_resource_group.rg_datasources.name}"
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



# resource "random_id" "randomId" {
#     keepers = {
#         # Generate a new ID whenever a new resource group is defined
#         resource_group = "${var.resource_group}"
#     }
#     byte_length = 8
# }

resource "random_string" "password" {
  length = 16
  special = true
}

resource "azurerm_key_vault_secret" "vm_laqn_admin_password" {
  name         = "vm-laqn-admin-password"
  value        = "${random_string.password.result}"
  key_vault_id = "${azurerm_key_vault.kvcleanairpasswords.id}"
}

resource "azurerm_public_ip" "vm_laqn_publicip" {
    name                         = "VM_LAQN_PublicIP"
    location                     = "${var.location}"
    resource_group_name          = "${azurerm_resource_group.rg_datasources.name}"
    allocation_method            = "Dynamic"
    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_network_interface" "vm_laqn_nic" {
    name                      = "VM_LAQN_NIC"
    location                  = "${var.location}"
    resource_group_name       = "${azurerm_resource_group.rg_datasources.name}"
    network_security_group_id = "${azurerm_network_security_group.cleanair_nsg.id}"

    ip_configuration {
        name                          = "NICCFG_CLEANAIR"
        subnet_id                     = "${azurerm_subnet.cleanair_subnet.id}"
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id          = "${azurerm_public_ip.cleanair_LAQN_publicip.id}"
    }

    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_virtual_machine" "vm_laqn" {
    name                  = "VM_LAQN"
    location              = "${var.location}"
    resource_group_name   = "${azurerm_resource_group.rg_datasources.name}"
    network_interface_ids = ["${azurerm_network_interface.vm_laqn_nic.id}"]
    vm_size               = "Standard_DS1_v2"

    storage_os_disk {
        name              = "VM_LAQN_OSDISK"
        caching           = "ReadWrite"
        create_option     = "FromImage"
        managed_disk_type = "Standard_LRS"
    }

    storage_image_reference {
        publisher = "Canonical"
        offer     = "UbuntuServer"
        sku       = "18.04-LTS"
        version   = "latest"
    }

    os_profile {
        computer_name  = "VM-LAQN"
        admin_username = "atiadmin"
        admin_password = "${azurerm_key_vault_secret.vm_laqn_admin_password.value}"
    }

    os_profile_linux_config {
      disable_password_authentication = false
    }

    boot_diagnostics {
        enabled     = "true"
        storage_uri = "${azurerm_storage_account.cleanair_storageaccount.primary_blob_endpoint}"
    }

    tags {
        environment = "Terraform Clean Air"
    }
}


