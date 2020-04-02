# # DATABASE USERS (Other users should be created manually.)


# TO ADD READ_WRITE USERS ADD A USERNAME TO THE LIST BELOW
variable "read_write_users" {
  description = "users"
  type = list(string)
  default = [
    "ogiles",
    "jrobinson",
    "pohara",
    "ohamelijnck",
    "jwalsh",
    "cluster",
  ]
}

# Initial_password
resource "random_string" "read_write_passwords" {
  count = "${length(var.read_write_users)}"
  keepers = {
    resource_group = "${var.resource_group}"
  }
  length  = 20
  special = true
}

# :: store the initial passwords in the keyvault
resource "azurerm_key_vault_secret" "db_read_write_usernames" {
  count        = "${length(var.read_write_users)}"
  name         = "${var.db_name}-db-${element(var.read_write_users, count.index)}-username"
  value        = "${element(var.read_write_users, count.index)}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

resource "azurerm_key_vault_secret" "db_read_write_passwords" {
  count        = "${length(var.read_write_users)}"
  name         = "${var.db_name}-db-${element(var.read_write_users, count.index)}-password"
  value        = "${random_string.read_write_passwords[count.index].result}"
  key_vault_id = "${var.key_vault_id}"
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Databases / Postgres"
  }
}

# Create the roles in postgres
resource "postgresql_role" "postgres_read_write_users" {
  count    = "${length(var.read_write_users)}"
  name     = "${element(var.read_write_users, count.index)}"
  login    = true
  password = "${random_string.read_write_passwords[count.index].result}"
  roles    = ["${postgresql_role.read_write.name}"]

}
