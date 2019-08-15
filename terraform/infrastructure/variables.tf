# Setup variables
variable "resource_group" {
  description = "Name of the resource group which infrastructure will be placed in"
}
variable "registry_admin_username_secret" {
  default = "container-registry-admin-username"
}
variable "registry_admin_password_secret" {
  default = "container-registry-admin-password"
}
variable "registry_login_server_secret" {
  default = "container-registry-login-server"
}
