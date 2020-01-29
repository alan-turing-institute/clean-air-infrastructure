# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}


# locals {
#   rg_scope = "/subscriptions/${module.configuration.subscription_id}/resourcegroups/${var.resource_group}"
# }


data "azurerm_resource_group" "this" {
  name = "${var.resource_group}"
}

# resource "azurerm_resource_group" "example" {
#   name     = "locked-resource-group"
#   location = "West Europe"
# }

# resource "azurerm_management_lock" "resource-group-level" {
#   name       = "resource-group-level"
#   scope      =
#   lock_level = "ReadOnly"
#   notes      = "This Resource Group is Read-Only"
# }



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

# :: create a role with appropriate permissions to run container instances
resource "azurerm_role_definition" "configure_kubernetes" {
  name        = "Configure Kubernetes"
  # scope       = "${local.rg_scope}"
  scope       = "${data.azurerm_resource_group.this.id}"
  description = "Configure Kubernetes cluster"

  permissions {
    actions = [
      "Microsoft.ContainerService/managedClusters/accessProfiles/listCredential/action",
      "Microsoft.ContainerService/managedClusters/listClusterUserCredential/action"
    ]
    not_actions = []
  }
  assignable_scopes = [
    "${data.azurerm_resource_group.this.id}"
  ]
}
data "azurerm_role_definition" "kubernetes_cluster_user" {
  name = "Azure Kubernetes Service Cluster User Role"
}

# ##[error]Error: Cannot download access profile/kube config file for the cluster cleanair-kubernetes.
# Reason The client '90f9b685-9e8c-486a-b52b-703ea3f22d78' with object id '90f9b685-9e8c-486a-b52b-703ea3f22d78' does not have authorization to perform
# action 'Microsoft.ContainerService/managedClusters/accessProfiles/listCredential/action' over
# scope '/subscriptions/edab2992-222c-4caa-949b-e64e56e6b61f/resourceGroups/RG_CLEANAIR_DATA_COLLECTION'/providers/Microsoft.ContainerService/managedClusters/cleanair-kubernetes/accessProfiles/clusterUser' or the scope is invalid. If access was recently granted, please refresh your credentials. (CODE: 403).


# :: grant the service principal the "configure_kubernetes" role
resource "azurerm_role_assignment" "service_principal_configure_kubernetes" {
  scope              = "${data.azurerm_resource_group.this.id}"
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
