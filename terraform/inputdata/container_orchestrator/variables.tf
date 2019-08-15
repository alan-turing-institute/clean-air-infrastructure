# Setup variables
variable "boot_diagnostics_uri" {}
variable "registry_server" {}
variable "inputs_db_admin_name_secret" {}
variable "inputs_db_admin_password_secret" {}
variable "key_vault_id" {}
variable "key_vault_name" {}
variable "nsg_id" {}
variable "resource_group" {}
variable "subnet_id" {}

# Derived variables
locals {
  admin_username = "atiadmin"
  machine        = "container-orchestrator"
  username       = "dockerdaemon"
}