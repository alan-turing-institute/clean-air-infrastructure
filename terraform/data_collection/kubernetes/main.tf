# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}


locals {
  rg_scope = "/subscriptions/${module.configuration.subscription_id}/resourcegroups/${var.resource_group}"
}

# Deploy a Kubernetes cluster
# ---------------------------
resource "azurerm_kubernetes_cluster" "this" {
  name                = "${var.cluster_name}"
  location            = "${module.configuration.location}"
  resource_group_name = "${var.resource_group}"
  dns_prefix          = "${var.cluster_name}"

  default_node_pool {
    name            = "default"
    node_count      = 1
    vm_size         = "Standard_D2_v2"
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

# Set permissions for the pre-existing service principal
# ------------------------------------------------------
data "azuread_service_principal" "this" {
  application_id = "${module.configuration.azure_service_principal_id}"
}

# # :: create a role with appropriate permissions to run container instances
# resource "azurerm_role_definition" "configure_kubernetes" {
#   name        = "Configure Kubernetes"
#   scope       = "${local.rg_scope}"
#   description = "Configure Kubernetes cluster"

#   permissions {
#     actions = [
#       "Microsoft.ContainerService/managedClusters/listClusterUserCredential/action",
#       "Microsoft.ContainerService/managedClusters/accessProfiles/listCredential/action"
#     ]
#     not_actions = []
#   }
#   assignable_scopes = [
#     "${local.rg_scope}"
#   ]
# }


data "azurerm_role_definition" "kubernetes_cluster_user" {
  name = "Azure Kubernetes Service Cluster User Role"
}


# :: grant the service principal the "configure_kubernetes" role
resource "azurerm_role_assignment" "service_principal_configure_kubernetes" {
  scope              = "${local.rg_scope}"
  # role_definition_id = "${azurerm_role_definition.configure_kubernetes.id}"
  role_definition_id = "${data.azurerm_role_definition.kubernetes_cluster_user.id}"
  principal_id       = "${data.azuread_service_principal.this.id}"
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
