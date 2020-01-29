# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}

# Deploy a Kubernetes cluster
# ---------------------------
resource "azurerm_kubernetes_cluster" "this" {
  name                = "${var.cluster_name}"
  location            = "${module.configuration.location}"
  resource_group_name = "${var.resource_group}"
  dns_prefix          = "${var.cluster_name}"

  agent_pool_profile {
    name            = "default"
    count           = 1
    vm_size         = "Standard_D2_v2"
    os_type         = "Linux"
    os_disk_size_gb = 30
  }

  service_principal {
    client_id     = "${module.configuration.azure_service_principal_id}"
    client_secret = "${module.configuration.azure_service_principal_password}"
  }

  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Kubernetes"
  }
}

# Set permissions for managed identity
# ------------------------------------
# :: create a role with appropriate permissions to run container instances
resource "azurerm_role_definition" "configure_kubernetes" {
  name        = "Configure Kubernetes"
  scope       = "${local.rg_data_collection_scope}"
  description = "Configure Kubernetes cluster"

  permissions {
    actions = [
      "Microsoft.ContainerService/managedClusters/listClusterUserCredential/action"
    ]
    not_actions = []
  }
  assignable_scopes = [
    "${local.rg_data_collection_scope}"
  ]
}
# :: grant the service principal the "configure_kubernetes" role
resource "azurerm_role_assignment" "service_principal_configure_kubernetes" {
  scope              = "${local.rg_data_collection_scope}"
  role_definition_id = "${azurerm_role_definition.configure_kubernetes.id}"
  principal_id       = "${module.configuration.azure_service_principal_id}"
}
# # :: grant the managed identity for this VM "ACRPull" access to the container registry
# resource "azurerm_role_assignment" "orchestrator_get_image" {
#   scope                = "${var.infrastructure.containers.id}"
#   role_definition_name = "AcrPull"
#   principal_id         = "${local.orchestrator_identity}"
# }
# # :: grant the managed identity for this VM "get" and "list" access to the key vault
# resource "azurerm_key_vault_access_policy" "allow_orchestrator" {
#   key_vault_id = "${var.infrastructure.key_vault.id}"
#   tenant_id    = "${module.configuration.tenant_id}"
#   object_id    = "${local.orchestrator_identity}"
#   key_permissions = [
#     "get",
#     "list",
#   ]
#   secret_permissions = [
#     "get",
#     "list",
#   ]
# }




# output "client_certificate" {
#   value = azurerm_kubernetes_cluster.this.kube_config.0.client_certificate
# }

# output "kube_config" {
#   value = azurerm_kubernetes_cluster.this.kube_config_raw
# }
