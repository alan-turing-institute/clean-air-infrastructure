# Derived variables
locals {
  admin_username = "atiadmin"
  username       = "${var.datasource}daemon"
  servername     = "cleanair-${var.datasource}"
}

# Generate random strings that persist for the lifetime of the resource group
# NB. we cannot tie these to the creation of the VM, since this creates a dependency cycle
resource "random_string" "vm_admin" {
  keepers = {
    resource_group = "${var.resource_group}"
  }

  length  = 16
  special = true
}

resource "random_string" "vm_github" {
  keepers = {
    resource_group = "${var.resource_group}"
  }

  length  = 16
  special = true
}

# Store the admin password in the keyvault
resource "azurerm_key_vault_secret" "vm_admin_password" {
  name         = "${var.datasource}-vm-admin-password"
  value        = "${random_string.vm_admin.result}"
  key_vault_id = "${var.keyvault_id}"
}

resource "azurerm_key_vault_secret" "vm_github_secret" {
  name         = "${var.datasource}-vm-github-secret"
  value        = "${random_string.vm_github.result}"
  key_vault_id = "${var.keyvault_id}"
}

# Create a public IP for the VM
resource "azurerm_public_ip" "vm_public_ip" {
  name                = "${upper("${var.datasource}")}-PUBLICIP"
  domain_name_label   = "${local.servername}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  allocation_method   = "Dynamic"

  tags {
    environment = "Terraform Clean Air"
  }
}

# Create a network card for the VM
resource "azurerm_network_interface" "vm_nic" {
  name                      = "${upper("${var.datasource}")}-NIC"
  location                  = "${var.location}"
  resource_group_name       = "${var.resource_group}"
  network_security_group_id = "${var.nsg_id}"

  ip_configuration {
    name                          = "${upper("${var.datasource}")}-NICCFG"
    subnet_id                     = "${var.subnet_id}"
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = "${azurerm_public_ip.vm_public_ip.id}"
  }

  tags {
    environment = "Terraform Clean Air"
  }
}

# Replace templated variables in the apache config file
data "template_file" "apache_config" {
  template = "${file("${path.module}/github_webhook/provisioning/apache.conf")}"

  vars {
    servername = "${local.servername}"
  }
}

data "template_file" "db_secrets" {
  template = "${file("${path.module}/github_webhook/provisioning/.db_secrets.json")}"
  vars {
    db_host = "${azurerm_postgresql_server.db_server.name}"
    db_name = "${azurerm_postgresql_database.postgres_database.name}"
    db_username = "${azurerm_postgresql_server.db_server.administrator_login}"
    db_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  }
}

data "template_file" "update_application" {
  template = "${file("${path.module}/github_webhook/provisioning/update_application.sh")}"

  vars {
    host = "${var.acr_login_server}"
    password = "${var.acr_admin_password}"
    username = "${var.acr_admin_user}"
    datasource = "${var.datasource}"
  }

}

data "template_file" "download_and_insert_data" {
  template = "${file("${path.module}/github_webhook/provisioning/download_and_insert_data.sh")}"

  vars {
    host = "${var.acr_login_server}"
    password = "${var.acr_admin_password}"
    username = "${var.acr_admin_user}"
    datasource = "${var.datasource}"
  }

}

# Replace templated variables in the cloud-init config file
data "template_file" "github_webhook" {
  template = "${file("${path.module}/github_webhook/cloudinit.tpl.yaml")}"

  vars {
    username   = "${local.username}"
    servername = "${local.servername}"

    # NB. the indentation of six spaces here ensures that the file will be inserted at the correct indentation level in the YAML file
    apache_config      = "${indent(6, "${data.template_file.apache_config.rendered}")}"
    flask_webhook      = "${indent(6, "${file("${path.module}/github_webhook/provisioning/flask_webhook.py")}")}"
    flask_wsgi         = "${indent(6, "${file("${path.module}/github_webhook/provisioning/flask_wsgi.py")}")}"
    update_application = "${indent(6, "${data.template_file.update_application.rendered}")}"
    download_and_insert_data = "${indent(6, "${data.template_file.download_and_insert_data.rendered}")}"
    github_known_hosts = "${indent(6, "${file("${path.module}/github_webhook/provisioning/known_hosts")}")}"
    github_secret      = "${indent(6, "${azurerm_key_vault_secret.vm_github_secret.value}")}"
    db_secrets         = "${indent(6, "${data.template_file.db_secrets.rendered}")}"
  }
}

# Build cloud-config configuration file from fragments
data "template_cloudinit_config" "cloudinit_config" {
  part {
    filename     = "cloudinit.yaml"
    content_type = "text/cloud-config"
    content      = "${data.template_file.github_webhook.rendered}"
  }

  part {
    content_type = "text/cloud-config"
    content      = "${file("${path.module}/cloudinit/${var.datasource}.yaml")}"
    merge_type   = "${var.cloud_init_merge}"
  }
}

# Create the VM
resource "azurerm_virtual_machine" "vm" {
  name                          = "${upper("${var.datasource}")}-VM"
  delete_os_disk_on_termination = true
  location                      = "${var.location}"
  resource_group_name           = "${var.resource_group}"
  network_interface_ids         = ["${azurerm_network_interface.vm_nic.id}"]
  vm_size                       = "Standard_DS1_v2"

  storage_os_disk {
    name              = "${upper("${var.datasource}")}-OSDISK"
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
    computer_name  = "${upper("${var.datasource}")}-VM"
    admin_username = "${local.admin_username}"
    admin_password = "${azurerm_key_vault_secret.vm_admin_password.value}"
    custom_data    = "${data.template_cloudinit_config.cloudinit_config.rendered}"
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
