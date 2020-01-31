# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "postgres" {
  value = module.postgres
}
output "resource_group_name" {
  value = "${azurerm_resource_group.this.name}"
}
