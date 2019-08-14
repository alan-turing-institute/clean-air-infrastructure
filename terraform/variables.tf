# Setup variables
variable "rg_databases" {
  description = "Resource group for databases"
  default = "RG_CLEANAIR_DATABASES"
}
variable "rg_input_data" {
  description = "Resource group for data collection"
  default = "RG_CLEANAIR_INPUT_DATA"
}
variable "rg_infrastructure" {
  description = "Resource group for infrastructure"
  default = "RG_CLEANAIR_INFRASTRUCTURE"
}