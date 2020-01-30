# Load configuration module
# -------------------------
module "configuration" {
  source = "../../configuration"
}

# Load data sources
# -----------------
data "azuread_service_principal" "this" {
  application_id = "${module.configuration.azure_service_principal_id}"
}

# Deploy the Kubernetes cluster resource group
# --------------------------------------------
resource "azurerm_resource_group" "this" {
  name     = var.cluster_resource_group
  location = module.configuration.location
  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data"
  }
}

# Deploy a Kubernetes cluster
# ---------------------------
resource "azurerm_kubernetes_cluster" "this" {
  name                = "${var.cluster_name}"
  location            = "${module.configuration.location}"
  resource_group_name = "${azurerm_resource_group.this.name}"
  dns_prefix          = "${var.cluster_name}"
  node_resource_group = "${var.node_resource_group}"

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

  addon_profile {
    kube_dashboard {
      enabled = true
    }
  }

  role_based_access_control {
    enabled = false
  }

  tags = {
    environment = "Terraform Clean Air"
    segment     = "Input data / Kubernetes"
  }
}

# Set permissions for the pre-existing service principal
# ------------------------------------------------------
# :: create a role with appropriate permissions for Kubernetes clusters
resource "azurerm_role_definition" "configure_kubernetes" {
  name        = "Configure Kubernetes"
  scope       = "${azurerm_resource_group.this.id}"
  description = "Configure Kubernetes cluster"

  permissions {
    actions = [
      "Microsoft.ContainerService/managedClusters/accessProfiles/listCredential/action",
      "Microsoft.ContainerService/managedClusters/listClusterUserCredential/action",
      "Microsoft.ContainerService/managedClusters/read"
    ]
    not_actions = []
  }
  assignable_scopes = [
    "${azurerm_resource_group.this.id}"
  ]
}

# :: grant the service principal the "configure_kubernetes" role
resource "azurerm_role_assignment" "service_principal_configure_kubernetes" {
  scope              = "${azurerm_resource_group.this.id}"
  role_definition_id = "${azurerm_role_definition.configure_kubernetes.id}"
  principal_id       = "${data.azuread_service_principal.this.id}"
}
