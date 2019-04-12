provider "azurerm" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=1.24"
  # subscription_id = "45a2ea24-e10c-4c35-b172-4b956deffbf2"
  subscription_id = "${var.subscription_id}"
}

provider "random" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=2.1"
}

# # Create a resource group
# resource "azurerm_resource_group" "cleanair_infrastructure_rg" {
#   name     = "RG_CLEANAIR_INFRASTRUCTURE"
#   location = "uksouth"
#   tags {
#       environment = "Terraform Clean Air"
#   }
# }

resource "random_id" "randomId" {
    keepers = {
        # Generate a new ID only when a new resource group is defined
        resource_group = "${var.resource_group}"
    }
    
    byte_length = 8
}

resource "azurerm_storage_account" "cleanair_storageaccount" {
    name                = "${random_id.randomId.hex}"
    resource_group_name = "${var.resource_group}"
    location            = "uksouth"
    account_replication_type = "LRS"
    account_tier = "Standard"

    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_storage_container" "clean_air_terraform_backend" {
  name                  = "terraform-backend"
  resource_group_name   = "${var.resource_group}"
  storage_account_name  = "${azurerm_storage_account.cleanair_storageaccount.name}"
  container_access_type = "private"
}

resource "azurerm_storage_blob" "clean_air_terraform_backend_blob" {
  name = "terraform-backend-blob"

  resource_group_name    = "${var.resource_group}"
  storage_account_name   = "${azurerm_storage_account.cleanair_storageaccount.name}"
  storage_container_name = "${azurerm_storage_container.clean_air_terraform_backend.name}"

  type = "page"
  size = 5120
}

resource "random_string" "password" {
  length = 16
  special = true
  override_special = "/@\" "
}

resource "azurerm_key_vault" "vm_laqn_keyvault" {
  name                        = "kvpasswords"
  location                    = "uksouth"
  resource_group_name         = "${var.resource_group}"
  tenant_id = "4395f4a7-e455-4f95-8a9f-1fbaef6384f9"
  sku {
    name = "standard"
  }

  access_policy {
    tenant_id = "4395f4a7-e455-4f95-8a9f-1fbaef6384f9"
    object_id = "3725de10-3768-4902-8bf3-2602d00101a2"
    key_permissions = [
      "create",
      "get",
    ]

    secret_permissions = [
      "set",
      "get",
      "delete",
    ]
  }
}

resource "azurerm_key_vault_secret" "cleanair_LAQN_set_password" {
  name  = "laqn-admin-password"
  value = "${random_string.password.result}"
  key_vault_id = "${azurerm_key_vault.vm_laqn_keyvault.id}"
}

resource "azurerm_virtual_network" "cleanair_vnet" {
    name                = "VNET_CLEANAIR"
    address_space       = ["10.0.0.0/16"]
    location            = "uksouth"
    resource_group_name = "${var.resource_group}"

    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_subnet" "cleanair_subnet" {
    name                 = "SUBNET_CLEANAIR"
    resource_group_name  = "${var.resource_group}"
    virtual_network_name = "${azurerm_virtual_network.cleanair_vnet.name}"
    address_prefix       = "10.0.2.0/24"
}

resource "azurerm_public_ip" "cleanair_LAQN_publicip" {
    name                         = "LAQN_PublicIP"
    location                     = "uksouth"
    resource_group_name          = "${var.resource_group}"
    allocation_method            = "Dynamic"

    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_network_security_group" "cleanair_nsg" {
    name                = "NSG_CLEANAIR"
    location            = "uksouth"
    resource_group_name = "${var.resource_group}"
    
    security_rule {
        name                       = "SSH"
        priority                   = 1001
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "22"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    tags {
        environment = "Terraform Clean Air"
    }
}

resource "azurerm_network_interface" "cleanair_LAQN_nic" {
    name                = "NIC_CLEANAIR"
    location            = "uksouth"
    resource_group_name = "${var.resource_group}"
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

resource "azurerm_virtual_machine" "cleanair_LAQN_vm" {
    name                  = "VM-LAQN"
    location              = "uksouth"
    resource_group_name   = "${var.resource_group}"
    network_interface_ids = ["${azurerm_network_interface.cleanair_LAQN_nic.id}"]
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
        admin_password = "${azurerm_key_vault_secret.cleanair_LAQN_set_password.value}"
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


