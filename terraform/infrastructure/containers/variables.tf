# Input variables
# ---------------
variable "key_vault" {}
variable "location" {}
variable "resource_group" {}
variable "admin_username_keyname" {
  default = "container-registry-admin-username"
}
variable "admin_password_keyname" {
  default = "container-registry-admin-password"
}
variable "login_server_keyname" {
  default = "container-registry-login-server"
}