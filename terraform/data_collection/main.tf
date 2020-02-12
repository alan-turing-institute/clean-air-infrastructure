# Load configuration module
module "configuration" {
  source = "../configuration"
}

# Set up a Kubernetes cluster to orchestrate the containers
module "kubernetes" {
  source                 = "./kubernetes"
  cluster_name           = "cleanair-kubernetes"
  service_hostname       = "urbanair.turing.ac.uk"
  cluster_resource_group = var.cluster_resource_group
  infrastructure         = "${var.infrastructure}"
  node_resource_group    = var.node_resource_group
}


# # Set up the necessary networking infrastructure
# module "networking" {
#   source         = "./networking"
#   resource_group = "${azurerm_resource_group.this.name}"
# }

# # Set up a virtual machine to orchestrate the containers
# module "container_orchestrator" {
#   source         = "./container_orchestrator"
#   databases      = "${var.databases}"
#   infrastructure = "${var.infrastructure}"
#   machine_name   = "cleanair-orchestrator"
#   networking     = module.networking
#   resource_group = "${azurerm_resource_group.data_collection.name}"
# }

