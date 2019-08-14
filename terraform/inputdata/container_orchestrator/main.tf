# Load configuration module
module "configuration" {
  source = "../../configuration"
}

# Generate an admin password that persists for the lifetime of the resource group
resource "random_string" "admin_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 16
  special = true
}
resource "azurerm_key_vault_secret" "orchestrator_admin_password" {
  name         = "${local.machine}-admin-password"
  value        = "${random_string.admin_password.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

# Generate a GitHub secret that persists for the lifetime of the resource group
resource "random_string" "github_secret" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 16
  special = true
}
resource "azurerm_key_vault_secret" "orchestrator_github_secret" {
  name         = "${local.machine}-github-secret"
  value        = "${random_string.github_secret.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

# Create a public IP for the VM
resource "azurerm_public_ip" "orchestrator" {
  name                = "${local.machine}-public-ip"
  domain_name_label   = "${local.machine}"
  location            = "${module.configuration.location}"
  resource_group_name = "${var.resource_group}"
  allocation_method   = "Dynamic"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

# Create a network card for the VM
resource "azurerm_network_interface" "orchestrator" {
  name                      = "${local.machine}-network-card"
  location                  = "${module.configuration.location}"
  resource_group_name       = "${var.resource_group}"
  network_security_group_id = "${var.nsg_id}"

  ip_configuration {
    name                          = "${local.machine}-ip-configuration"
    subnet_id                     = "${var.subnet_id}"
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = "${azurerm_public_ip.orchestrator.id}"
  }
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

data "external" "latest_commit_hash" {
  program = ["bash", "${path.module}/provisioning/commit_hash.sh"]
}

# Replace templated variables:
# ... apache config file
data "template_file" "apache_config" {
  template = "${file("${path.module}/templates/apache.template.conf")}"
  vars = {
    servername = "${local.machine}"
  }
}
# ... application runner
data "template_file" "run_application" {
  template = "${file("${path.module}/templates/run_application.template.sh")}"
  vars = {
    key_vault_id     = "${var.key_vault_id}"
    resource_group  = "${var.resource_group}"
    registry_server = "${var.registry_server}"
  }
}
# # ... database secrets
# data "local_file" "db_secrets" {
#   filename = "${path.module}/../../.secrets/.db_inputs_secret.json"
# }
# ... cloud-init config file
data "template_file" "cloudinit" {
  template = "${file("${path.module}/templates/cloudinit.template.yaml")}"
  vars = {
    username           = "${local.username}"
    servername         = "${local.machine}"
    latest_commit_hash = "${data.external.latest_commit_hash.result.hash}"
    # NB. the indentation of six spaces here ensures that the file will be inserted at the correct indentation level in the YAML file
    apache_config      = "${indent(6, "${data.template_file.apache_config.rendered}")}"
    flask_webhook      = "${indent(6, "${file("${path.module}/provisioning/flask_webhook.py")}")}"
    flask_wsgi         = "${indent(6, "${file("${path.module}/provisioning/flask_wsgi.py")}")}"
    run_application    = "${indent(6, "${data.template_file.run_application.rendered}")}"
    github_known_hosts = "${indent(6, "${file("${path.module}/provisioning/known_hosts")}")}"
    github_secret      = "${indent(6, "${azurerm_key_vault_secret.orchestrator_github_secret.value}")}"
    # db_secrets         = "${indent(6, "${data.local_file.db_secrets.content}")}"
  }
}

# Create the VM
resource "azurerm_virtual_machine" "orchestrator" {
  name                          = "${local.machine}-vm"
  delete_os_disk_on_termination = true
  location                      = "${module.configuration.location}"
  resource_group_name           = "${var.resource_group}"
  network_interface_ids         = ["${azurerm_network_interface.orchestrator.id}"]
  vm_size                       = "Standard_B1s"

  boot_diagnostics {
    enabled     = true
    storage_uri = "${var.boot_diagnostics_uri}"
  }

  identity {
    type = "SystemAssigned"
  }

  os_profile {
    computer_name  = "${local.machine}-vm"
    admin_username = "${local.admin_username}"
    admin_password = "${azurerm_key_vault_secret.orchestrator_admin_password.value}"
    custom_data    = "${data.template_file.cloudinit.rendered}"
  }

  os_profile_linux_config {
    disable_password_authentication = false
  }

  storage_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }

  storage_os_disk {
    name              = "${local.machine}-osdisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

# Give the managed identity for this VM access to the key vault
data "azurerm_subscription" "primary" {}
resource "azurerm_role_assignment" "orchestrator" {
  scope                = "${data.azurerm_subscription.primary.id}"
  role_definition_name = "Reader"
  principal_id         = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
}

resource "azurerm_key_vault_access_policy" "allow_orchestrator" {
  key_vault_id = "${var.key_vault_id}"
  tenant_id    = "${module.configuration.tenant_id}"
  object_id    = "${azurerm_role_assignment.orchestrator.principal_id}"
  key_permissions = [
    "get",
    "list",
  ]
  secret_permissions = [
    "get",
    "list",
  ]
}
