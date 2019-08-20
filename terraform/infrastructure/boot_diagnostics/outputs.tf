# Outputs which are useful to later Terraform scripts
# ---------------------------------------------------
output "primary_blob_endpoint" {
  value = "${azurerm_storage_account.this.primary_blob_endpoint}"
}