
# CREATE SCHEMAS AND ASSIGN ROLES (SELECT, INSERT, UPDATE, DELETE, RULE, REFERENCES, TRIGGER, CREATE, TEMPORARY, EXECUTE, and USAGE)
# Dynamic data
resource "postgresql_schema" "schema_dynamic_data" {
  name  = "dynamic_data"
}

resource postgresql_grant "read_only_dynamic_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  schema      = "${postgresql_schema.schema_dynamic_data.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

resource postgresql_grant "read_write_dynamic_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  schema      = "${postgresql_schema.schema_dynamic_data.name}"
  object_type = "table"
  privileges  = ["ALL"]
}

resource postgresql_grant "read_write_api_dynamic_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write_api.name}"
  schema      = "${postgresql_schema.schema_dynamic_data.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

# Interest points
resource "postgresql_schema" "schema_interest_points" {
  name  = "interest_points"
}
resource postgresql_grant "read_only_interest_points" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  schema      = "${postgresql_schema.schema_interest_points.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

resource postgresql_grant "read_write_interest_points" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  schema      = "${postgresql_schema.schema_interest_points.name}"
  object_type = "table"
  privileges  = ["ALL"]
}

resource postgresql_grant "read_write_api_interest_points" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write_api.name}"
  schema      = "${postgresql_schema.schema_interest_points.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

# Model features
resource "postgresql_schema" "schema_model_features" {
  name  = "model_features"
}

resource postgresql_grant "read_only_model_features" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  schema      = "${postgresql_schema.schema_model_features.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

resource postgresql_grant "read_write_model_features" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  schema      = "${postgresql_schema.schema_model_features.name}"
  object_type = "table"
  privileges  = ["ALL"]
}

# Model results
resource "postgresql_schema" "schema_model_results" {
  name  = "model_results"
}

resource postgresql_grant "read_only_model_results" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  schema      = "${postgresql_schema.schema_model_results.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

resource postgresql_grant "read_write_model_results" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  schema      = "${postgresql_schema.schema_model_results.name}"
  object_type = "table"
  privileges  = ["ALL"]
}

resource postgresql_grant "read_write_api_model_results" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write_api.name}"
  schema      = "${postgresql_schema.schema_model_results.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

# Processed data
resource "postgresql_schema" "my_schema" {
  name  = "processed_data"
}

resource "postgresql_schema" "schema_processed_data" {
  name  = "processed_data"
}

resource postgresql_grant "read_only_processed_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  schema      = "${postgresql_schema.schema_processed_data.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

resource postgresql_grant "read_write_processed_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  schema      = "${postgresql_schema.schema_processed_data.name}"
  object_type = "table"
  privileges  = ["ALL"]
}

resource "postgresql_schema" "schema_static_data" {
  name  = "static_data"

}

resource postgresql_grant "read_only_static_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_all.name}"
  schema      = "${postgresql_schema.schema_static_data.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}

resource postgresql_grant "read_write_static_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write.name}"
  schema      = "${postgresql_schema.schema_static_data.name}"
  object_type = "table"
  privileges  = ["ALL"]
}

resource postgresql_grant "read_write_api_static_data" {
  database    = "${azurerm_key_vault_secret.db_name.value}"
  role        = "${postgresql_role.read_write_api.name}"
  schema      = "${postgresql_schema.schema_static_data.name}"
  object_type = "table"
  privileges  = ["SELECT"]
}
