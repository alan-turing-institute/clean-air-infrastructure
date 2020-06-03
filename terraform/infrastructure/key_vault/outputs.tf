# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "id" {
  value = "${azurerm_key_vault.this.id}"
}
output "name" {
  value = "${azurerm_key_vault.this.name}"
}
output "scoot_aws_key_id_keyname" {
  value = "${azurerm_key_vault_secret.scoot_aws_key_id.name}"
}
output "scoot_aws_key_keyname" {
  value = "${azurerm_key_vault_secret.scoot_aws_key.name}"
}