# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "inputs" {
  value = module.inputs
}
output "resource_group_name" {
  value = "${azurerm_resource_group.this.name}"
}
