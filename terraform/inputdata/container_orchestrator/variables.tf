# Setup variables
variable "acr_admin_password" {}
variable "acr_admin_user" {}
variable "acr_login_server" {}
variable "keyvault_id" {}
variable "location" {}
variable "nsg_id" {}
variable "resource_group" {}
variable "subnet_id" {}

# Derived variables
locals {
  admin_username = "atiadmin"
  machine        = "container-orchestrator"
  username       = "dockerdaemon"
}