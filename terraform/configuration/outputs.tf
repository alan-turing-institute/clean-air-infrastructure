# Read SCOOT AWS keys from the configuration key vault and expose them as outputs
# :: subscription ID
data "external" "subscription_id" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "subscription-id", "--query", "{value: value}"]
}
output "subscription_id" {
  description = "ID of the Azure subscription to deploy into"
  value       = "${data.external.subscription_id.result.value}"
}
# :: tenant ID
data "external" "tenant_id" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "tenant-id", "--query", "{value: value}"]
}
output "tenant_id" {
  description = "ID of a tenant with appropriate permissions to create infrastructure"
  value       = "${data.external.tenant_id.result.value}"
}
# :: location
data "external" "location" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "location", "--query", "{value: value}"]
}
output "location" {
  description = "Name of the Azure location to build in"
  value       = "${data.external.location.result.value}"
}
# :: Azure group ID
data "external" "azure_group_id" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "azure-group-id", "--query", "{value: value}"]
}
output "azure_group_id" {
  description = "ID of a group containing all accounts that will be allowed to access the infrastructure"
  value       = "${data.external.azure_group_id.result.value}"
}
# :: Azure service principal name
data "external" "azure_service_principal_name" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "azure-service-principal-name", "--query", "{value: value}"]
}
output "azure_service_principal_name" {
  description = "Name of the service principal used by the Kubernetes cluster"
  value       = "${data.external.azure_service_principal_name.result.value}"
}
# :: Azure service principal id
data "external" "azure_service_principal_id" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "azure-service-principal-id", "--query", "{value: value}"]
}
output "azure_service_principal_id" {
  description = "ID of the service principal used by the Kubernetes cluster"
  value       = "${data.external.azure_service_principal_id.result.value}"
}
# :: Azure service principal password
data "external" "azure_service_principal_password" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "azure-service-principal-password", "--query", "{value: value}"]
}
output "azure_service_principal_password" {
  description = "Password for the service principal used by the Kubernetes cluster"
  value       = "${data.external.azure_service_principal_password.result.value}"
}
# :: SCOOT AWS key
data "external" "scoot_aws_key" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "scoot-aws-key", "--query", "{value: value}"]
}
output "scoot_aws_key" {
  description = "AWS key for accessing TfL SCOOT data"
  value       = "${data.external.scoot_aws_key.result.value}"
}
# :: SCOOT AWS key ID
data "external" "scoot_aws_key_id" {
  program = ["az", "keyvault", "secret", "show", "--vault-name", "terraform-configuration", "--name", "scoot-aws-key-id", "--query", "{value: value}"]
}
output "scoot_aws_key_id" {
  description = "AWS key ID for accessing TfL SCOOT data"
  value       = "${data.external.scoot_aws_key_id.result.value}"
}
