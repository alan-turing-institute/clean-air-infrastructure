# Create the infrastructure resource group
resource "azurerm_resource_group" "rg_infrastructure" {
  name     = "${var.resource_group}"
  location = "${var.location}"

  tags {
    environment = "Terraform Clean Air"
  }
}

# Generate a random string that persists for the lifetime of the resource group
resource "random_string" "lower_case_letters_bootdiagnostics" {
  keepers = {
    resource_group = "${azurerm_resource_group.rg_infrastructure.name}"
  }

  length  = 9
  number  = false
  special = false
  upper   = false
}

# Generate a random string that persists for the lifetime of the resource group
resource "random_string" "lower_case_letters_keyvaultname" {
  keepers = {
    resource_group = "${azurerm_resource_group.rg_infrastructure.name}"
  }

  length  = 6
  number  = false
  special = false
  upper   = false
}

# Create the keyvault where passwords are stored
resource "azurerm_key_vault" "kvcleanairpasswords" {
  name                = "kvcleanairpass${random_string.lower_case_letters_keyvaultname.result}"
  location            = "${var.location}"
  resource_group_name = "${azurerm_resource_group.rg_infrastructure.name}"
  tenant_id           = "${var.tenant_id}"

  sku {
    name = "standard"
  }

  access_policy {
    tenant_id = "${var.tenant_id}"
    object_id = "${var.azure_group_id}"

    key_permissions = [
      "create",
      "delete",
      "get",
      "list",
    ]

    secret_permissions = [
      "set",
      "delete",
      "get",
      "list",
    ]
  }

  tags {
    environment = "Terraform Clean Air"
  }
}

# Create storage account for boot diagnostics
resource "azurerm_storage_account" "bootdiagnostics" {
  name                     = "bootdiagnostics${random_string.lower_case_letters_bootdiagnostics.result}"
  resource_group_name      = "${azurerm_resource_group.rg_infrastructure.name}"
  location                 = "${var.location}"
  account_replication_type = "LRS"
  account_tier             = "Standard"

  tags {
    environment = "Terraform Clean Air"
  }
}

# Provide outputs which are useful to later Terraform scripts
output "keyvault_id" {
  value = "${azurerm_key_vault.kvcleanairpasswords.id}"
}

output "boot_diagnostics_uri" {
  value = "${azurerm_storage_account.bootdiagnostics.primary_blob_endpoint}"
}


# Create azure container registry
resource "azurerm_container_registry" "acr" {
  name                     = "CleanAirTestContainerRegistry"
  resource_group_name      = "${azurerm_resource_group.rg_infrastructure.name}"
  location                 = "${var.location}"
  sku                      = "Basic"
  admin_enabled            = true
}


