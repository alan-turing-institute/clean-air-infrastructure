# Generate a random string that persists for the lifetime of the resource group
# NB. we cannot tie this to the creation of the VM, since this creates a dependency cycle
resource "random_string" "alphanumeric_with_special_laqn" {
  keepers = {
      resource_group = "${azurerm_resource_group.rg_cleanair_datasources.name}"
  }
  length = 16
  special = true
}


# Store the admin password in the keyvault
resource "azurerm_key_vault_secret" "laqn_vm_admin_password" {
  name         = "laqn-vm-admin-password"
  value        = "${random_string.alphanumeric_with_special_laqn.result}"
  key_vault_id = "${var.keyvault_id}"
}

# Create a public IP for the LAQN VM
resource "azurerm_public_ip" "laqn_public" {
    name                         = "LAQN-PUBLICIP"
    location                     = "${var.location}"
    resource_group_name          = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    allocation_method            = "Dynamic"
    tags {
        environment = "Terraform Clean Air"
    }
}

# Create a network card for the LAQN VM
resource "azurerm_network_interface" "laqn_nic" {
    name                      = "LAQN-NIC"
    location                  = "${var.location}"
    resource_group_name       = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    network_security_group_id = "${azurerm_network_security_group.nsg_cleanair_datasources.id}"

    ip_configuration {
        name                          = "LAQN-NICCFG"
        subnet_id                     = "${azurerm_subnet.subnet_cleanair_datasources.id}"
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id          = "${azurerm_public_ip.laqn_public.id}"
    }

    tags {
        environment = "Terraform Clean Air"
    }
}

# Create the LAQN VM
resource "azurerm_virtual_machine" "laqn_vm" {
    name                          = "LAQN-VM"
    delete_os_disk_on_termination = true
    location                      = "${var.location}"
    resource_group_name           = "${azurerm_resource_group.rg_cleanair_datasources.name}"
    network_interface_ids         = ["${azurerm_network_interface.laqn_nic.id}"]
    vm_size                       = "Standard_DS1_v2"

    storage_os_disk {
        name              = "LAQN-OSDISK"
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
        computer_name  = "LAQN-VM"
        admin_username = "atiadmin"
        admin_password = "${azurerm_key_vault_secret.laqn_vm_admin_password.value}"
        custom_data    = "${file("${path.module}/cloudinit/laqn.yaml")}"
    }

    os_profile_linux_config {
      disable_password_authentication = false
    }

    boot_diagnostics {
        enabled     = "true"
        storage_uri = "${var.boot_diagnostics_uri}"
    }

    # Copies the laqn script folder to /home/laqndaemon/ on the remote VM
    provisioner "file" {
        source      = "${path.module}/../../scripts/datasources/laqn/laqn_test.py"
        destination = "/laqn_test.py"

        connection {
            type     = "ssh"
            user     = "atiadmin"
            password = "${azurerm_key_vault_secret.laqn_vm_admin_password.value}"
        }
    }

    tags {
        environment = "Terraform Clean Air"
    }
}

output "path" {
    value = "${path.module}/../../scripts/datasources/laqn/"
}