# Create a random admin password each time the network card is created
# NB. we cannot tie this to the creation of the VM, since this creates a dependency cycle
resource "random_string" "password" {
  keepers = {
    network_card = "${azurerm_network_interface.vm_laqn_nic.name}"
  }
  length = 16
  special = true
}

# Store the admin password in the keyvault
resource "azurerm_key_vault_secret" "vm_laqn_admin_password" {
  name         = "vm-laqn-admin-password"
  value        = "${random_string.password.result}"
  key_vault_id = "${var.keyvault_id}"
}

# Create a public IP for the LAQN VM
resource "azurerm_public_ip" "vm_laqn_publicip" {
    name                         = "VM_LAQN_PublicIP"
    location                     = "${var.location}"
    resource_group_name          = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    allocation_method            = "Dynamic"
    tags {
        environment = "Terraform Clean Air"
    }
}

# Create a network card for the LAQN VM
resource "azurerm_network_interface" "vm_laqn_nic" {
    name                      = "VM_LAQN_NIC"
    location                  = "${var.location}"
    resource_group_name       = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    network_security_group_id = "${azurerm_network_security_group.nsg_cleanair_datasources.id}"

    ip_configuration {
        name                          = "NICCFG_CLEANAIR"
        subnet_id                     = "${azurerm_subnet.subnet_cleanair_datasources.id}"
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id          = "${azurerm_public_ip.vm_laqn_publicip.id}"
    }

    tags {
        environment = "Terraform Clean Air"
    }
}

# Create the LAQN VM
resource "azurerm_virtual_machine" "vm_laqn" {
    name                  = "VM_LAQN"
    location              = "${var.location}"
    resource_group_name   = "${azurerm_resource_group.rg_cleanair_datasources.name}"
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
        computer_name  = "VM_LAQN"
        admin_username = "atiadmin"
        admin_password = "${azurerm_key_vault_secret.vm_laqn_admin_password.value}"
    }

    os_profile_linux_config {
      disable_password_authentication = false
    }

    boot_diagnostics {
        enabled     = "true"
        storage_uri = "${var.boot_diagnostics_uri}"
    }

    tags {
        environment = "Terraform Clean Air"
    }
}


