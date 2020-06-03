# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "boot_diagnostics" {
  value = module.boot_diagnostics
}
output "containers" {
  value = module.containers
}
output "key_vault" {
  value = module.key_vault
}
output "resource_group_name" {
  value = "${azurerm_resource_group.this.name}"
}