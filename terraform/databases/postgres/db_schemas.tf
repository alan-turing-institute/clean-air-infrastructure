
# CREATE SCHEMAS AND ASSIGN ROLES (SELECT, INSERT, UPDATE, DELETE, RULE, REFERENCES, TRIGGER, CREATE, TEMPORARY, EXECUTE, and USAGE)
# Define schemas


variable "cleanair_schemas" {
  description = "Schema"
  type = list(string)
  default = [
    "dynamic_data",
    "interest_points",
    "model_features",
    "model_results",
    "processed_data",
    "static_data"
  ]
}

# Create schemas and ensure role groups have usage
resource "postgresql_schema" "schemas" {
  count = "${length(var.cleanair_schemas)}"
  name  = "${element(var.cleanair_schemas, count.index)}"
  policy {
    usage = true
    create = true
    role  = "${postgresql_role.read_write.name}"
  }
  policy {
    usage = true
    role  = "${postgresql_role.read_all.name}"
  }
}


# Grant privileges to group roles
resource postgresql_grant "read_write_privileges" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  count       = "${length(var.cleanair_schemas)}"
  schema      = "${element(var.cleanair_schemas, count.index)}"
  object_type = "table"
  privileges  = ["ALL"]
}

resource postgresql_grant "read_privileges" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  count       = "${length(var.cleanair_schemas)}"
  schema      = "${element(var.cleanair_schemas, count.index)}"
  object_type = "table"
  privileges  = ["SELECT"]
}

