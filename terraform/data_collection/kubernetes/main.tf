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

# output "client_certificate" {
#   value = azurerm_kubernetes_cluster.this.kube_config.0.client_certificate
# }

# output "kube_config" {
#   value = azurerm_kubernetes_cluster.this.kube_config_raw
# }
