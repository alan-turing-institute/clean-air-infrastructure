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
  name         = "${var.machine_name}-admin-password"
  value        = "${random_string.admin_password.result}"
  key_vault_id = "${var.infrastructure.key_vault_id}"
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
  name         = "${var.machine_name}-github-secret"
  value        = "${random_string.github_secret.result}"
  key_vault_id = "${var.infrastructure.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

# Create a public IP for the VM
resource "azurerm_public_ip" "orchestrator" {
  name                = "${var.machine_name}-public-ip"
  domain_name_label   = "${var.machine_name}"
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
  name                      = "${var.machine_name}-network-card"
  location                  = "${module.configuration.location}"
  resource_group_name       = "${var.resource_group}"
  network_security_group_id = "${var.networking.nsg_id}"

  ip_configuration {
    name                          = "${var.machine_name}-ip-configuration"
    subnet_id                     = "${var.networking.subnet_id}"
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
    servername = "${var.machine_name}"
  }
}
# ... application runner
data "template_file" "run_application" {
  template = "${file("${path.module}/templates/run_application.template.sh")}"
  vars = {
    db_admin_password_secret       = "${var.databases.inputs_db_admin_password_secret}"
    db_admin_username_secret       = "${var.databases.inputs_db_admin_name_secret}"
    db_server_name_secret          = "${var.databases.inputs_db_server_name_secret}"
    key_vault_name                 = "${var.infrastructure.key_vault_name}"
    registry_admin_password_secret = "${var.infrastructure.registry_admin_password_secret}"
    registry_admin_username_secret = "${var.infrastructure.registry_admin_username_secret}"
    registry_server                = "${var.infrastructure.registry_server}"
    resource_group                 = "${var.resource_group}"
  }
}


# ... cloud-init config file
data "template_file" "cloudinit" {
  template = "${file("${path.module}/templates/cloudinit.template.yaml")}"
  vars = {
    username           = "${var.username}"
    servername         = "${var.machine_name}"
    latest_commit_hash = "${data.external.latest_commit_hash.result.hash}"
    # NB. the indentation of six spaces here ensures that the file will be inserted at the correct indentation level in the YAML file
    apache_config      = "${indent(6, "${data.template_file.apache_config.rendered}")}"
    flask_webhook      = "${indent(6, "${file("${path.module}/provisioning/flask_webhook.py")}")}"
    flask_wsgi         = "${indent(6, "${file("${path.module}/provisioning/flask_wsgi.py")}")}"
    run_application    = "${indent(6, "${data.template_file.run_application.rendered}")}"
    github_known_hosts = "${indent(6, "${file("${path.module}/provisioning/known_hosts")}")}"
    github_secret      = "${indent(6, "${azurerm_key_vault_secret.orchestrator_github_secret.value}")}"
  }
}

# Create the VM
resource "azurerm_virtual_machine" "orchestrator" {
  name                          = "${var.machine_name}-vm"
  delete_os_disk_on_termination = true
  location                      = "${module.configuration.location}"
  resource_group_name           = "${var.resource_group}"
  network_interface_ids         = ["${azurerm_network_interface.orchestrator.id}"]
  vm_size                       = "Standard_B1s"

  boot_diagnostics {
    enabled     = true
    storage_uri = "${var.infrastructure.boot_diagnostics_uri}"
  }

  identity {
    type = "SystemAssigned"
  }

  os_profile {
    computer_name  = "${var.machine_name}-vm"
    admin_username = "${var.admin_username}"
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
    name              = "${var.machine_name}-osdisk"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }

  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}

locals {
  orchestrator_identity = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
}

# Grant the managed identity for this VM "Reader" access to the subscription
data "azurerm_subscription" "primary" {}
resource "azurerm_role_assignment" "orchestrator_on_rg_input_data" {
  scope                = "/subscriptions/45a2ea24-e10c-4c35-b172-4b956deffbf2/resourcegroups/RG_CLEANAIR_INPUT_DATA"
  role_definition_name = "Owner"
  # principal_id         = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
  principal_id         = "${local.orchestrator_identity}"
}

resource "azurerm_role_assignment" "orchestrator_on_rg_infrastructure" {
  scope                = "/subscriptions/45a2ea24-e10c-4c35-b172-4b956deffbf2/resourcegroups/RG_CLEANAIR_INFRASTRUCTURE"
  role_definition_name = "Reader"
  # principal_id         = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
  principal_id         = "${local.orchestrator_identity}"
}

resource "azurerm_role_assignment" "orchestrator_on_key_vault" {
  scope                = "${var.infrastructure.key_vault_id}"
  role_definition_name = "Reader"
  # principal_id         = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
  principal_id         = "${local.orchestrator_identity}"
}

# Grant the managed identity for this VM "ACRPull" access to the container registry
resource "azurerm_role_assignment" "orchestrator_on_container_registry" {
  scope                = "${var.infrastructure.registry_id}"
  role_definition_name = "AcrPull"
  # principal_id         = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
  principal_id         = "${local.orchestrator_identity}"
}

# Grant the managed identity for this VM "get" and "list" access to the key vault
resource "azurerm_key_vault_access_policy" "allow_orchestrator" {
  key_vault_id = "${var.infrastructure.key_vault_id}"
  tenant_id    = "${module.configuration.tenant_id}"
  # object_id    = "${lookup(azurerm_virtual_machine.orchestrator.identity[0], "principal_id")}"
  object_id    = "${local.orchestrator_identity}"
  key_permissions = [
    "get",
    "list",
  ]
  secret_permissions = [
    "get",
    "list",
  ]
}
