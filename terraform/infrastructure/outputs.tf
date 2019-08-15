# Provide outputs which are useful to later Terraform scripts
# output "acr_admin_user" {
#   value = "${azurerm_container_registry.cleanair.admin_username}"
# }
# output "acr_admin_password" {
#   value = "${azurerm_container_registry.cleanair.admin_password}"
# }
output "registry_id" {
  value = "${azurerm_container_registry.cleanair.id}"
}
output "registry_admin_username_secret" {
  value = "${var.registry_admin_username_secret}"
}
output "registry_admin_password_secret" {
  value = "${var.registry_admin_password_secret}"
}
output "registry_server" {
  value = "${azurerm_container_registry.cleanair.login_server}"
}
output "key_vault_id" {
  value = "${azurerm_key_vault.cleanair.id}"
}
output "key_vault_name" {
  value = "${azurerm_key_vault.cleanair.name}"
}
output "boot_diagnostics_uri" {
  value = "${azurerm_storage_account.bootdiagnostics.primary_blob_endpoint}"
}