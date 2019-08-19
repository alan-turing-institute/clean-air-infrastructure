# Provide outputs which are useful to later Terraform scripts
output "boot_diagnostics_uri" {
  value = "${azurerm_storage_account.bootdiagnostics.primary_blob_endpoint}"
}
output "key_vault_id" {
  value = "${azurerm_key_vault.cleanair.id}"
}
output "key_vault_name" {
  value = "${azurerm_key_vault.cleanair.name}"
}
output "registry_id" {
  value = "${azurerm_container_registry.cleanair.id}"
}
output "registry_admin_username_keyname" {
  value = "${var.registry_admin_username_keyname}"
}
output "registry_admin_password_keyname" {
  value = "${var.registry_admin_password_keyname}"
}
output "registry_server" {
  value = "${azurerm_container_registry.cleanair.login_server}"
}
output "resource_group_name" {
  value = "${azurerm_resource_group.this.name}"
}