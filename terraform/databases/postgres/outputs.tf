# Provide outputs which are useful to later Terraform scripts
output "db_name" {
  value = "${azurerm_postgresql_database.this.name}"
}
output "db_admin_name_secret" {
  value = "${azurerm_key_vault_secret.db_admin_name.name}"
}
output "db_admin_password_secret" {
  value = "${azurerm_key_vault_secret.db_admin_password.name}"
}
output "db_server_name_secret" {
  value = "${azurerm_key_vault_secret.db_server_name.name}"
}