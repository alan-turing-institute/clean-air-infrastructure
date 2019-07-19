locals {
  admin_username = "atiadmin_${var.datasource}"

    version   = "latest"
  }


# Generate random strings that persist for the lifetime of the resource group
# NB. we cannot tie these to the creation of the VM, since this creates a dependency cycle
resource "random_string" "db_password" {
  keepers = {
    resource_group = "${var.resource_group_db}"
  }
  length  = 16
  special = true
}

resource "random_string" "db_admin" {
  keepers = {
    resource_group = "${var.resource_group_db}"
  }

  length  = 16
  special = true
}



resource "azurerm_key_vault_secret" "db_admin_password" {
  name         = "${var.datasource}-db-admin-password"
  value        = "${random_string.db_password.result}"
  key_vault_id = "${var.keyvault_id}"
}

resource "azurerm_postgresql_server" "db_server" {
  name                = "${lower("${var.datasource}")}-server"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group_db}"

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

  administrator_login          = "${local.admin_username}"
  administrator_login_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  version                      = "9.6"
  ssl_enforcement              = "Enabled"
}

resource "azurerm_postgresql_database" "postgres_database" {
  name                = "${lower("${var.datasource}")}_db"
  resource_group_name = "${var.resource_group_db}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

resource "azurerm_postgresql_firewall_rule" "azure_ips" {
  name                = "allow-all-azure-ips"
  resource_group_name = "${var.resource_group_db}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

resource "azurerm_postgresql_firewall_rule" "azure_ips_desktop" {
  name                = "allow-turing-desktop-ips"
  resource_group_name = "${var.resource_group_db}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "193.60.220.240"
  end_ip_address      = "193.60.220.240"
}

resource "azurerm_postgresql_firewall_rule" "azure_ips_wifi" {
  name                = "allow-turing-wifi-ips"
  resource_group_name = "${var.resource_group_db}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "193.60.220.253"
  end_ip_address      = "193.60.220.253"
}

resource "azurerm_postgresql_firewall_rule" "oscar_ips_wifi" {
  name                = "allow-oscar-wifi-ips"
  resource_group_name = "${var.resource_group_db}"
  server_name         = "${azurerm_postgresql_server.db_server.name}"
  start_ip_address    = "94.12.116.182"
  end_ip_address      = "94.12.116.182"
}


data "template_file" "database_secrets" {
  template = "${file("${path.module}/database_setup/provisioning/.db_secrets.json")}"
  vars {
    db_host = "${azurerm_postgresql_server.db_server.name}"
    db_name = "${azurerm_postgresql_database.postgres_database.name}"
    db_username = "${azurerm_postgresql_server.db_server.administrator_login}"
    db_password = "${azurerm_key_vault_secret.db_admin_password.value}"
  }
}

resource "local_file" "database_secrets_file" {
    sensitive_content     = "${data.template_file.database_secrets.rendered}"
    filename = "${path.cwd}/.secrets/.${lower("${var.datasource}")}_secret.json"
}
