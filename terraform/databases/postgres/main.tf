# Store the DB server name in the keyvault
resource "azurerm_key_vault_secret" "db_server_name" {
  name         = "${var.db_name}-db-server-name"
  value        = "${lower("${var.db_name}")}-server"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}
# Store the DB admin name in the keyvault
resource "azurerm_key_vault_secret" "db_admin_name" {
  name         = "${var.db_name}-db-admin-name"
  value        = "atiadmin_${var.db_name}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

# Create the DB admin password
resource "random_string" "db_admin_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 16
  special = true
}
# ... and store it in the key vault
resource "azurerm_key_vault_secret" "db_admin_password" {
  name         = "${var.db_name}-db-admin-password"
  value        = "${random_string.db_admin_password.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}


# Create the database server
resource "azurerm_postgresql_server" "db_server" {
  name                = "${azurerm_key_vault_secret.db_server_name.value}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"

  sku {
    name     = "B_Gen5_2"
    capacity = 2
    tier     = "Basic"
    family   = "Gen5"
  }

  storage_profile {
    storage_mb            = "${var.db_size}"
    backup_retention_days = 7
    geo_redundant_backup  = "Disabled"
  }

  administrator_login          = "${azurerm_key_vault_secret.db_admin_name.value}"
  administrator_login_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  version                      = "9.6"
  ssl_enforcement              = "Enabled"

  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

# Create the database
resource "azurerm_postgresql_database" "this" {
  name                = "${lower("${var.db_name}")}_db"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

resource "azurerm_postgresql_firewall_rule" "azure_ips" {
  name                = "allow-all-azure-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

resource "azurerm_postgresql_firewall_rule" "turing_ips_desktop" {
  name                = "allow-turing-desktop-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "193.60.220.240"
  end_ip_address      = "193.60.220.240"
}

resource "azurerm_postgresql_firewall_rule" "turing_ips_wifi" {
  name                = "allow-turing-wifi-ips"
  resource_group_name = "${var.resource_group}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "193.60.220.253"
  end_ip_address      = "193.60.220.253"
}

data "template_file" "database_secrets" {
  template = "${file("${path.module}/templates/db_secrets.template.json")}"
  vars = {
    db_host = "${azurerm_postgresql_server.db_server.name}"
    db_name = "${azurerm_postgresql_database.this.name}"
    db_username = "${azurerm_postgresql_server.db_server.administrator_login}"
    db_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  }
}

resource "local_file" "database_secrets_file" {
  sensitive_content = "${data.template_file.database_secrets.rendered}"
  filename          = "${path.cwd}/.secrets/.db_${lower("${var.db_name}")}_secret.json"
}
