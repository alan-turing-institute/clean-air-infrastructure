# Provide outputs which are useful to later Terraform scripts
output "db_admin_name" {
  value = "${azurerm_key_vault_secret.db_admin_name.value}"
}
output "db_admin_password" {
  value = "${azurerm_key_vault_secret.db_admin_password.value}"
}
