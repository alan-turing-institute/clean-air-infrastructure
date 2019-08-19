# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}

# Create azure container registry and upload the secrets to travis
# ----------------------------------------------------------------
resource "azurerm_container_registry" "this" {
  name                = "CleanAirContainerRegistry"
  resource_group_name = "${var.resource_group}"
  location            = "${var.location}"
  sku                 = "Basic"
  admin_enabled       = true

  provisioner "local-exec" {
    command = "travis env set ACR_SERVER ${azurerm_container_registry.this.login_server} --private"
  }
  provisioner "local-exec" {
    command = "travis env set ACR_USERNAME ${azurerm_container_registry.this.admin_username} --private"
  }
  provisioner "local-exec" {
    command = "travis env set ACR_PASSWORD ${azurerm_container_registry.this.admin_password} --private"
  }
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}

# # Write the container registry secrets to file
# resource "local_file" "acr_secret" {
#   sensitive_content = "${azurerm_container_registry.this.login_server}\n${azurerm_container_registry.this.admin_username}\n${azurerm_container_registry.this.admin_password}"
#   filename          = "${path.cwd}/.secrets/.acr_secret.json"
# }

# Write the container registry secrets to the key vault
# -----------------------------------------------------
resource "azurerm_key_vault_secret" "this_login_server" {
  name         = "${var.login_server_keyname}"
  value        = "${azurerm_container_registry.this.login_server}"
  key_vault_id = "${var.key_vault.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}
resource "azurerm_key_vault_secret" "this_admin_password" {
  name         = "${var.admin_password_keyname}"
  value        = "${azurerm_container_registry.this.admin_password}"
  key_vault_id = "${var.key_vault.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}
resource "azurerm_key_vault_secret" "this_admin_username" {
  name         = "${var.admin_username_keyname}"
  value        = "${azurerm_container_registry.this.admin_username}"
  key_vault_id = "${var.key_vault.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}



