
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


# # Assign permissions

# variable "read_only_" {
#   description = "User name."
#   type = "list"
#   default = [
#     "test1",
#     "test2",
#     "test3",
#     "test4",
#     "test5",
#     "test6"
#   ]
# }



# resource postgresql_grant "read_only_dynamic_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_all.name}"
#   schema      = "${postgresql_schema.schema_dynamic_data.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# resource postgresql_grant "read_write_dynamic_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write.name}"
#   schema      = "${postgresql_schema.schema_dynamic_data.name}"
#   object_type = "table"
#   privileges  = ["ALL"]
# }

# resource postgresql_grant "read_write_api_dynamic_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write_api.name}"
#   schema      = "${postgresql_schema.schema_dynamic_data.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# # Interest points
# }
# resource postgresql_grant "read_only_interest_points" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_all.name}"
#   schema      = "${postgresql_schema.schema_interest_points.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# resource postgresql_grant "read_write_interest_points" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write.name}"
#   schema      = "${postgresql_schema.schema_interest_points.name}"
#   object_type = "table"
#   privileges  = ["ALL"]
# }

# resource postgresql_grant "read_write_api_interest_points" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write_api.name}"
#   schema      = "${postgresql_schema.schema_interest_points.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# # Model features


# resource postgresql_grant "read_only_model_features" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_all.name}"
#   schema      = "${postgresql_schema.schema_model_features.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# resource postgresql_grant "read_write_model_features" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write.name}"
#   schema      = "${postgresql_schema.schema_model_features.name}"
#   object_type = "table"
#   privileges  = ["ALL"]
# }

# # Model results
# resource postgresql_grant "read_only_model_results" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_all.name}"
#   schema      = "${postgresql_schema.schema_model_results.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# resource postgresql_grant "read_write_model_results" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write.name}"
#   schema      = "${postgresql_schema.schema_model_results.name}"
#   object_type = "table"
#   privileges  = ["ALL"]
# }

# resource postgresql_grant "read_write_api_model_results" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write_api.name}"
#   schema      = "${postgresql_schema.schema_model_results.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# # Processed data

# resource postgresql_grant "read_only_processed_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_all.name}"
#   schema      = "${postgresql_schema.schema_processed_data.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# resource postgresql_grant "read_write_processed_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write.name}"
#   schema      = "${postgresql_schema.schema_processed_data.name}"
#   object_type = "table"
#   privileges  = ["ALL"]
# }



# resource postgresql_grant "read_only_static_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_all.name}"
#   schema      = "${postgresql_schema.schema_static_data.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }

# resource postgresql_grant "read_write_static_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write.name}"
#   schema      = "${postgresql_schema.schema_static_data.name}"
#   object_type = "table"
#   privileges  = ["ALL"]
# }

# resource postgresql_grant "read_write_api_static_data" {
#   database    = "${azurerm_key_vault_secret.db_name.value}"
#   role        = "${postgresql_role.read_write_api.name}"
#   schema      = "${postgresql_schema.schema_static_data.name}"
#   object_type = "table"
#   privileges  = ["SELECT"]
# }
