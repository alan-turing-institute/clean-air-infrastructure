# Setup variables
variable "boot_diagnostics_uri" {}
variable "registry_server" {}
variable "key_vault_id" {}
variable "nsg_id" {}
variable "resource_group" {}
variable "subnet_id" {}

# Derived variables
locals {
  admin_username = "atiadmin"
  machine        = "container-orchestrator"
  username       = "dockerdaemon"
}