# Setup variables
variable "rg_databases" {
  description = "Resource group for databases"
  default = "RG_CLEANAIR_DATABASES"
}
variable "rg_datasources" {
  description = "Resource group for datasources"
  default = "RG_CLEANAIR_DATASOURCES"
}
variable "rg_infrastructure" {
  description = "Resource group for infrastructure"
  default = "RG_CLEANAIR_INFRASTRUCTURE"
}