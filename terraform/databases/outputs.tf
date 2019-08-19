# Provide outputs which are useful to later Terraform scripts
# output "inputs_db_name" {
#   value = "${module.inputs.db_name}"
# }
# output "inputs_db_admin_name_keyname" {
#   value = "${module.inputs.db_admin_name_keyname}"
# }
# output "inputs_db_admin_password_keyname" {
#   value = "${module.inputs.db_admin_password_keyname}"
# }
# output "inputs_db_server_name_keyname" {
#   value = "${module.inputs.db_server_name_keyname}"
# }
output "inputs" {
  value = module.inputs
}
output "resource_group_name" {
  value = "${azurerm_resource_group.this.name}"
}
