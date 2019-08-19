output "subscription_id" {
  description = "ID of the Azure subscription to deploy into"
  value       = "45a2ea24-e10c-4c35-b172-4b956deffbf2"
}
output "tenant_id" {
  description = "ID of a tenant with appropriate permissions to create infrastructure"
  value       = "4395f4a7-e455-4f95-8a9f-1fbaef6384f9"
}
output "location" {
  description = "Name of the Azure location to build in"
  value       = "uksouth"
}
output "azure_group_id" {
  description = "ID of a group containing all accounts that will be allowed to access the infrastructure"
  value       = "35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c"
}
