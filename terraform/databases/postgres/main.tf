# Random strings
# --------------
# :: database admin password
resource "random_string" "db_admin_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}

# Key vault secrets
# -----------------
# :: store the database server name in the keyvault
resource "azurerm_key_vault_secret" "db_server_name" {
  name         = "${var.db_name}-db-server-name"
  value        = "${lower("${var.db_name}")}-server"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}
# :: store the database name in the keyvault
resource "azurerm_key_vault_secret" "db_name" {
  name         = "${var.db_name}-db-name"
  value        = "${replace(lower("${var.db_name}"), "-", "_")}_db"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}
# :: store the database admin name in the keyvault
resource "azurerm_key_vault_secret" "db_admin_username" {
  name         = "${var.db_name}-db-admin-username"
  value        = "atiadmin"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

# :: store the database admin password in the keyvault
resource "azurerm_key_vault_secret" "db_admin_password" {
  name         = "${var.db_name}-db-admin-password"
  value        = "${random_string.db_admin_password.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

# Database setup
# --------------
# :: convert the database size into MB
locals {
  db_size_mb = "${1024 * var.db_size_gb}"
}
# :: create the database server
resource "azurerm_postgresql_server" "this" {
  name                = "${azurerm_key_vault_secret.db_server_name.value}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  sku_name            = "MO_Gen5_4"

  storage_profile {
    storage_mb            = "${local.db_size_mb}"
    backup_retention_days = 7
    geo_redundant_backup  = "Disabled"
    auto_grow             = "Enabled"
  }

  administrator_login          = "${azurerm_key_vault_secret.db_admin_username.value}"
  administrator_login_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  version                      = "11"
  ssl_enforcement              = "Enabled"

  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }

  lifecycle {
    ignore_changes = [storage_profile[0].storage_mb]
  }
}

# :: create the database
resource "azurerm_postgresql_database" "this" {
  name                = "${azurerm_key_vault_secret.db_name.value}"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.this.name}"
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

# :: create firewall rules
resource "azurerm_postgresql_firewall_rule" "azure_ips" {
  name                = "allow-all-azure-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.this.name}"
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

resource "azurerm_postgresql_firewall_rule" "turing_ips_desktop" {
  name                = "allow-turing-desktop-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.this.name}"
  start_ip_address    = "193.60.220.240"
  end_ip_address      = "193.60.220.240"
}

resource "azurerm_postgresql_firewall_rule" "turing_ips_wifi" {
  name                = "allow-turing-wifi-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.this.name}"
  start_ip_address    = "193.60.220.253"
  end_ip_address      = "193.60.220.253"
}

# resource "azurerm_postgresql_firewall_rule" "gla_ips_wifi" {
#   name                = "allow-gla-wifi-ips"
#   resource_group_name = "${var.resource_group}"
#   server_name         = "${azurerm_postgresql_server.this.name}"
#   start_ip_address    = "195.99.240.222"
#   end_ip_address      = "195.99.240.222"
# }

# Add a provider so we can assign database roles (max_connections should be fairly large https://github.com/terraform-providers/terraform-provider-postgresql/issues/81)
provider "postgresql" {
  host            = "${azurerm_postgresql_server.this.name}.postgres.database.azure.com"
  database        = "${azurerm_key_vault_secret.db_name.value}"
  username        = "${azurerm_key_vault_secret.db_admin_username.value}@${azurerm_postgresql_server.this.name}"
  password        = "${azurerm_key_vault_secret.db_admin_password.value}"
  sslmode         = "require"
  connect_timeout = 15
  superuser = false
  max_connections = 20
}

# Add extentions
resource "postgresql_extension" "ext_postgis" {
  name = "postgis"
}

resource "postgresql_extension" "ext_uuid" {
  name = "uuid-ossp"
}

# Users
# Random strings
# --------------
# :: database admin password
resource "random_string" "db_cluster_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}

# :: store the database admin name in the keyvault
resource "azurerm_key_vault_secret" "db_cluster_username" {
  name         = "${var.db_name}-db-cluster-username"
  value        = "cluster"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

# :: store the database admin password in the keyvault
resource "azurerm_key_vault_secret" "db_cluster_password" {
  name         = "${var.db_name}-db-cluster-password"
  value        = "${random_string.db_cluster_password.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}
