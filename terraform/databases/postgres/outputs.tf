# Provide outputs which are useful to later Terraform scripts
output "this_db_name" {
  value = "${azurerm_postgresql_database.this.name}"
}
output "this_db_admin_name_keyname" {
  value = "${azurerm_key_vault_secret.db_admin_name.name}"
}
output "this_db_admin_password_keyname" {
  value = "${azurerm_key_vault_secret.db_admin_password.name}"
}
output "this_db_server_name_keyname" {
  value = "${azurerm_key_vault_secret.db_server_name.name}"
}