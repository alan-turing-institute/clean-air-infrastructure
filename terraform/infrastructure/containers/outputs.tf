# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "admin_username_keyname" {
  value = "${azurerm_key_vault_secret.this_admin_username.name}"
}
output "admin_password_keyname" {
  value = "${azurerm_key_vault_secret.this_admin_password.name}"
}
output "id" {
  value = "${azurerm_container_registry.this.id}"
}
output "server_name" {
  value = "${azurerm_container_registry.this.login_server}"
}
