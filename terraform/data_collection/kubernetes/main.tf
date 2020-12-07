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
  name                = var.cluster_name
  location            = "${module.configuration.location}"
  resource_group_name = "${azurerm_resource_group.this.name}"
  dns_prefix          = var.cluster_name
  node_resource_group = "${var.node_resource_group}"

  default_node_pool {
    name                = "default"
    enable_auto_scaling = true
    max_count           = 6
    min_count           = 1
    node_count          = 1
    vm_size             = "Standard_B8ms"
    os_disk_size_gb     = 30
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

resource "azurerm_kubernetes_cluster_node_pool" "jamcam_pool" {
  name                  = "jamcam"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = "Standard_NC24"
  enable_auto_scaling   = true
  max_count             = 4
  min_count             = 0
  node_count            = 4
  os_disk_size_gb       = 100
  node_taints           = ["group=gpu:NoSchedule"]
}


resource "azurerm_kubernetes_cluster_node_pool" "cleanair_pool" {
  name                  = "cleanair"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = "Standard_NC6"
  enable_auto_scaling   = false
  max_count             = 0
  min_count             = 0
  node_count            = 0
  os_disk_size_gb       = 100
  node_taints           = ["group=cleangpu:NoSchedule"]
}

resource "azurerm_kubernetes_cluster_node_pool" "cleanair_pool_gpu" {
  name                  = "cleanairgpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = "Standard_NC6"
  enable_auto_scaling   = true
  max_count             = 2
  min_count             = 0
  node_count            = 1
  os_disk_size_gb       = 100
  node_taints           = ["group=cleangpu:NoSchedule"]
}

resource "azurerm_kubernetes_cluster_node_pool" "jamcambf" {
  name                  = "jamcambf"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = "Standard_NC24"
  enable_auto_scaling   = true
  max_count             = 5
  min_count             = 0
  node_count            = 5
  os_disk_size_gb       = 100
  node_taints           = ["group=gpuBackFill:NoSchedule"]
}

resource "azurerm_kubernetes_cluster_node_pool" "jamcambf2" {
  name                  = "jamcambf"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = "Standard_NC24_Promo"
  enable_auto_scaling   = true
  max_count             = 7
  min_count             = 0
  node_count            = 7
  os_disk_size_gb       = 100
  node_taints           = ["group=gpuBackFill:NoSchedule"]
}

resource "azurerm_kubernetes_cluster_node_pool" "jamcambf3" {
  name                  = "jamcambf"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = "Standard_NC24sv3"
  enable_auto_scaling   = true
  max_count             = 4
  min_count             = 0
  node_count            = 4
  os_disk_size_gb       = 100
  node_taints           = ["group=gpuBackFill:NoSchedule"]
}

# Set permissions for the pre-existing service principal
# ------------------------------------------------------
# Create a role with appropriate permissions for Kubernetes clusters
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
# Grant the service principal the "configure_kubernetes" role
resource "azurerm_role_assignment" "service_principal_configure_kubernetes" {
  scope              = "${azurerm_resource_group.this.id}"
  role_definition_id = split("|", azurerm_role_definition.configure_kubernetes.id)[0]
  principal_id       = "${data.azuread_service_principal.this.id}"
}
# :: grant the managed identity for this VM "get" and "list" access to the key vault
resource "azurerm_key_vault_access_policy" "allow_service_principal" {
  key_vault_id = "${var.infrastructure.key_vault.id}"
  tenant_id    = "${module.configuration.tenant_id}"
  object_id    = "${data.azuread_service_principal.this.id}"
  key_permissions = [
    "get",
    "list",
  ]
  secret_permissions = [
    "get",
    "list",
  ]
}

# Add a DNS Zone for the api service
resource "azurerm_dns_zone" "cleanair_api_service" {
    name                = "${var.service_hostname}"
    resource_group_name = "${azurerm_resource_group.this.name}"
}