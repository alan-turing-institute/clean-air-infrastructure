# Generate random strings that persist for the lifetime of the resource group
# NB. we cannot tie these to the creation of the VM, since this creates a dependency cycle
resource "random_string" "db_password" {
  keepers = {
    network_card = "${var.resource_group}"
  }

  length  = 16
  special = true
}

resource "random_string" "db_admin" {
  keepers = {
    network_card = "${var.resource_group}"
  }

  length  = 16
  special = true
}

resource "azurerm_key_vault_secret" "db_admin_password" {
  name         = "${var.datasource}-db-admin-password"
  value        = "${random_string.db_password.result}"
  key_vault_id = "${var.keyvault_id}"
}

# # Write the password to file

# resource "local_file" "secrets" {
#   content  = "${azurerm_key_vault_secret.cleanair_LAQN_postgres_password.value}"
#   filename = ".secrets/laqn_server_pass.txt"
# }

resource "azurerm_postgresql_server" "db_server" {
  name                = "${lower("${var.datasource}")}-server"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"

  sku {
    name     = "B_Gen5_2"
    capacity = 2
    tier     = "Basic"
    family   = "Gen5"
  }

  storage_profile {
    storage_mb            = 5120
    backup_retention_days = 7
    geo_redundant_backup  = "Disabled"
  }

  administrator_login          = "${local.admin_username}"
  administrator_login_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  version                      = "9.5"
  ssl_enforcement              = "Enabled"
}

resource "azurerm_postgresql_database" "postgres_database" {
  name                = "${lower("${var.datasource}")}_db"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

# Allow access to server from azure resources (0.0.0.0 )
resource "azurerm_postgresql_firewall_rule" "azure_ips" {
  name                = "allow-all-azure-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

# Allow access to server from localhost (defined ib variables.tf)
# HACK - using Turing IP for testing, should be changed to azure
# resource "azurerm_postgresql_firewall_rule" "local_ips" {
#   name                = "allow-localhost-ip"
#   resource_group_name = "${var.resource_group}"
#   server_name         = "${azurerm_postgresql_server.db_server.name}"
#   start_ip_address    = "193.60.220.240"
#   end_ip_address      = "193.60.220.240"
# }

