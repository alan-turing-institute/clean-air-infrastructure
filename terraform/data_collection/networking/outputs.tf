
output "nsg_id" {
  value = "${azurerm_network_security_group.input_data.id}"
}
output "subnet_id" {
  value = "${azurerm_subnet.input_data.id}"
}
