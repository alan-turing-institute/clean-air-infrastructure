# Provide outputs which are useful to later Terraform scripts
output "id" {
  value = "${azurerm_key_vault.this.id}"
}
output "name" {
  value = "${azurerm_key_vault.this.name}"
}
