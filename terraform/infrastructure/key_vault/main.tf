# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}

# Create the keyvault where passwords are stored
# ----------------------------------------------
resource "azurerm_key_vault" "this" {
  name                = "cleanair-secrets"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  sku_name            = "standard"
  tenant_id           = "${module.configuration.tenant_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure"
  }
}

# # Allow members of the Azure group full access
# # --------------------------------------------
# resource "azurerm_key_vault_access_policy" "allow_group" {
#   key_vault_id = "${azurerm_key_vault.this.id}"
#   tenant_id    = "${module.configuration.tenant_id}"
#   object_id    = "${module.configuration.azure_group_id}"
#   key_permissions = [
#     "create",
#     "delete",
#     "get",
#     "list",
#   ]
#   secret_permissions = [
#     "set",
#     "delete",
#     "get",
#     "list",
#   ]
# }

# Write SCOOT AWS secrets to the keyvault
# ---------------------------------------
resource "azurerm_key_vault_secret" "scoot_aws_key_id" {
  name         = "scoot-aws-key-id"
  value        = "${module.configuration.scoot_aws_key_id}"
  key_vault_id = "${azurerm_key_vault.this.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure / Key Vault"
  }
}
# :: store the database admin name in the keyvault
resource "azurerm_key_vault_secret" "scoot_aws_key" {
  name         = "scoot-aws-key"
  value        = "${module.configuration.scoot_aws_key}"
  key_vault_id = "${azurerm_key_vault.this.id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Infrastructure / Key Vault"
  }
}