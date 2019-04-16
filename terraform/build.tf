module "common" {
  source         = "./common"
  location       = "${var.infrastructure_location}"
  object_id      = "${var.azure_group_id}"
  resource_group = "RG_CLEANAIR_INFRASTRUCTURE"
  tenant_id      = "${var.tenant_id}"
}
module "laqn" {
  source         = "./laqn"
  location       = "${var.infrastructure_location}"
  resource_group = "RG_CLEANAIR_DATASOURCES"
  keyvault_id    = "${module.common.keyvault_id}"
  # resource_group = "${var.infrastructure_resource_group}"
  # tenant_id       = "${var.tenant_id}"
}


# output "client_id" {
#     value = "${module.common.client_id}"
# }
# output "tenant_id" {
#     value = "${module.common.tenant_id}"
# }
# output "subscription_id " {
#     value = "${module.common.subscription_id}"
# }
