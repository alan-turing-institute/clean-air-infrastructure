# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "db_name" {
  value = "${azurerm_key_vault_secret.db_name.value}"
}
output "db_admin_username_keyname" {
  value = "${azurerm_key_vault_secret.db_admin_username.name}"
}
output "db_admin_password_keyname" {
  value = "${azurerm_key_vault_secret.db_admin_password.name}"
}
output "db_server_name_keyname" {
  value = "${azurerm_key_vault_secret.db_server_name.name}"
}