# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}

# Random strings
# --------------
# :: VM admin password
resource "random_string" "admin_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}
# :: GitHub secret
resource "random_string" "github_secret" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}

# Key vault secrets
# -----------------
# :: store the VM admin password in the key vault
resource "azurerm_key_vault_secret" "orchestrator_admin_password" {
  name         = "${var.machine_name}-admin-password"
  value        = "${random_string.admin_password.result}"
  key_vault_id = "${var.infrastructure.key_vault.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}
# :: store the GitHub secret in the key vault
resource "azurerm_key_vault_secret" "orchestrator_github_secret" {
  name         = "${var.machine_name}-github-secret"
  value        = "${random_string.github_secret.result}"
  key_vault_id = "${var.infrastructure.key_vault.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}



# Construct provisioning files from templates
# -------------------------------------------
# :: commit hash
data "external" "latest_commit_hash" {
  program = ["bash", "${path.module}/provisioning/commit_hash.sh"]
}
# :: apache config file
data "template_file" "apache_config" {
  template = "${file("${path.module}/templates/apache.template.conf")}"
  vars = {
    servername = "${var.machine_name}"
  }
}
# :: application runner
data "template_file" "run_application" {
  template = "${file("${path.module}/templates/run_application.template.sh")}"
  vars = {
    db_admin_password_keyname       = "${var.databases.inputs.db_admin_password_keyname}"
    db_admin_username_keyname       = "${var.databases.inputs.db_admin_username_keyname}"
    db_name                         = "${var.databases.inputs.db_name}"
    db_server_name_keyname          = "${var.databases.inputs.db_server_name_keyname}"
    key_vault_name                  = "${var.infrastructure.key_vault.name}"
    registry_admin_password_keyname = "${var.infrastructure.containers.admin_password_keyname}"
    registry_admin_username_keyname = "${var.infrastructure.containers.admin_username_keyname}"
    registry_server                 = "${var.infrastructure.containers.server_name}"
    resource_group                  = "${var.resource_group}"
    scoot_aws_key_id_keyname        = "${var.infrastructure.key_vault.scoot_aws_key_id_keyname}"
    scoot_aws_key_keyname           = "${var.infrastructure.key_vault.scoot_aws_key_keyname}"
  }
}
# :: cloud-init config file
data "template_file" "cloudinit" {
  template = "${file("${path.module}/templates/cloudinit.template.yaml")}"
  vars = {
    username           = "${var.username}"
    servername         = "${var.machine_name}"
    latest_commit_hash = "${data.external.latest_commit_hash.result.hash}"
    # NB. the indentation of six spaces here ensures that the file will be inserted at the correct indentation level in the YAML file
    apache_config      = "${indent(6, "${data.template_file.apache_config.rendered}")}"
    flask_webhook      = "${indent(6, "${file("${path.module}/provisioning/webhook.py")}")}"
    flask_app_wsgi     = "${indent(6, "${file("${path.module}/provisioning/app.wsgi")}")}"
    run_application    = "${indent(6, "${data.template_file.run_application.rendered}")}"
    github_known_hosts = "${indent(6, "${file("${path.module}/provisioning/known_hosts")}")}"
    github_secret      = "${indent(6, "${azurerm_key_vault_secret.orchestrator_github_secret.value}")}"
  }
}

# Create the orchestration VM
# ---------------------------
# :: create a public IP
resource "azurerm_public_ip" "this" {
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
# :: create a network card
resource "azurerm_network_interface" "this" {
  name                      = "${var.machine_name}-network-card"
  location                  = "${module.configuration.location}"
  resource_group_name       = "${var.resource_group}"
  network_security_group_id = "${var.networking.nsg_id}"

  ip_configuration {
    name                          = "${var.machine_name}-ip-configuration"
    subnet_id                     = "${var.networking.subnet_id}"
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = "${azurerm_public_ip.this.id}"
  }
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Container orchestrator"
  }
}
# :: create the VM
resource "azurerm_virtual_machine" "this" {
  name                          = "${var.machine_name}-vm"
  delete_os_disk_on_termination = true
  location                      = "${module.configuration.location}"
  resource_group_name           = "${var.resource_group}"
  network_interface_ids         = ["${azurerm_network_interface.this.id}"]
  vm_size                       = "Standard_B1s"

  boot_diagnostics {
    enabled     = true
    storage_uri = "${var.infrastructure.boot_diagnostics.primary_blob_endpoint}"
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
  orchestrator_identity    = "${lookup(azurerm_virtual_machine.this.identity[0], "principal_id")}"
  rg_data_collection_scope = "/subscriptions/${module.configuration.subscription_id}/resourcegroups/${var.resource_group}"
}

# Set permissions for managed identity
# ------------------------------------
# :: create a role with appropriate permissions to run container instances
resource "azurerm_role_definition" "run_containers" {
  name        = "Run containers"
  scope       = "${local.rg_data_collection_scope}"
  description = "Create and run container instances"

  permissions {
    actions = [
      "Microsoft.ContainerInstance/containerGroups/read",
      "Microsoft.ContainerInstance/containerGroups/write",
      "Microsoft.Resources/subscriptions/resourcegroups/read"
    ]
    not_actions = []
  }
  assignable_scopes = [
    "${local.rg_data_collection_scope}"
  ]
}
# :: grant the managed identity for this VM "Reader" access to create conainer
resource "azurerm_role_assignment" "orchestrator_run_container_instance" {
  scope              = "${local.rg_data_collection_scope}"
  role_definition_id = "${azurerm_role_definition.run_containers.id}"
  principal_id       = "${local.orchestrator_identity}"
}
# :: grant the managed identity for this VM "ACRPull" access to the container registry
resource "azurerm_role_assignment" "orchestrator_get_image" {
  scope                = "${var.infrastructure.containers.id}"
  role_definition_name = "AcrPull"
  principal_id         = "${local.orchestrator_identity}"
}
# :: grant the managed identity for this VM "get" and "list" access to the key vault
resource "azurerm_key_vault_access_policy" "allow_orchestrator" {
  key_vault_id = "${var.infrastructure.key_vault.id}"
  tenant_id    = "${module.configuration.tenant_id}"
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
