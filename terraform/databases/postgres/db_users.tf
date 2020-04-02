# DATABASE USERS (Other users should be created manually.)


# A user for the cluster
resource "random_string" "db_cluster_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}

# :: store the cluster username/password in the keyvault
resource "azurerm_key_vault_secret" "db_cluster_username" {
  name         = "${var.db_name}-db-custer-username"
  value        = "cleanaircluster"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

resource "azurerm_key_vault_secret" "db_cluster_password" {
  name         = "${var.db_name}-db-cluster-password"
  value        = "${random_string.db_cluster_password.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

resource "postgresql_role" "cluster_user" {
  name     = "cluster_user"
  login    = true
  password = "${random_string.db_cluster_password.result}"
  roles = ["${postgresql_role.read_write.name}"]

}

# A user for the api
resource "random_string" "db_api_password" {
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}

# :: store the cluster username/password in the keyvault
resource "azurerm_key_vault_secret" "db_api_username" {
  name         = "${var.db_name}-db-api-username"
  value        = "cleanairapi"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

resource "azurerm_key_vault_secret" "db_api_password" {
  name         = "${var.db_name}-db-api-password"
  value        = "${random_string.db_api_password.result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

resource "postgresql_role" "api_user" {
  name     = "api_user"
  login    = true
  password = "${random_string.db_api_password.result}"
  roles = ["${postgresql_role.read_write_api.name}"]

}