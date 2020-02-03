# Setup variables
variable "resource_group_databases" {
  description = "Resource group for databases"
  default     = "RG_CLEANAIR_DATABASES"
}
variable "resource_group_infrastructure" {
  description = "Resource group for infrastructure"
  default     = "RG_CLEANAIR_INFRASTRUCTURE"
}
variable "resource_group_k8s_cluster" {
  description = "Resource group for Kubernetes cluster"
  default     = "RG_CLEANAIR_KUBERNETES_CLUSTER"
}
variable "resource_group_k8s_nodes" {
  description = "Resource group for Kubernets data collecting/processing nodes"
  default     = "RG_CLEANAIR_KUBERNETES_NODES"
}