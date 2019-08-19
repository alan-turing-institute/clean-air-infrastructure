# Setup variables
variable "resource_group_databases" {
  description = "Resource group for databases"
  default     = "RG_CLEANAIR_DATABASES"
}
variable "resource_group_data_collection" {
  description = "Resource group for data collection"
  default     = "RG_CLEANAIR_DATA_COLLECTION"
}
variable "resource_group_infrastructure" {
  description = "Resource group for infrastructure"
  default     = "RG_CLEANAIR_INFRASTRUCTURE"
}