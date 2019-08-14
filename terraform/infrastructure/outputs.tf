# Provide outputs which are useful to later Terraform scripts
output "acr_admin_user" {
  value = "${azurerm_container_registry.cleanair.admin_username}"
}
output "acr_admin_password" {
  value = "${azurerm_container_registry.cleanair.admin_password}"
}
output "acr_login_server" {
  value = "${azurerm_container_registry.cleanair.login_server}"
}
output "keyvault_id" {
  value = "${azurerm_key_vault.cleanair.id}"
}