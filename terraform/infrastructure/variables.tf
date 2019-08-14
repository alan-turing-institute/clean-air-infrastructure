# Setup variables
variable "azure_group_id" {
  description = "ID of a group containing all accounts that will be allowed to access the infrastructure"
}
variable "location" {
  description = "Name of the Azure location to build in"
}
variable "resource_group" {
  description = "Name of the resource group which infrastructure will be placed in"
}
variable "tenant_id" {
  description = "ID of a tenant with appropriate permissions to create infrastructure"
}
