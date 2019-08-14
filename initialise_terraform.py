#! /usr/bin/env python
import argparse
import logging
import os
import random
import string
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
from azure.storage.blob import BlockBlobService


# Set up logging
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)

# Read command line arguments
parser = argparse.ArgumentParser(description='Initialise the Azure infrastructure needed by Terraform')
parser.add_argument("-g", "--resource-group", type=str, default="RG_TERRAFORM_BACKEND",
                    help="Resource group where the Terraform backend will be stored")
parser.add_argument("-l", "--location", type=str, default="uksouth",
                    help="Azure datacentre where the Terraform backend will be stored")
parser.add_argument("-s", "--storage-container-name", type=str, default="terraformbackend",
                    help="Name of the storage container where the Terraform backend will be stored")
parser.add_argument("-a", "--azure-group-id", type=str, default="35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c",
                    help="ID of an Azure group which contains all developers. Default is Turing's 'All Users' group.")
args = parser.parse_args()


def emphasised(text):
    return termcolor.colored(text, 'green')


def build_backend():
    # Get subscription
    _, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(subscription_id).display_name
    logging.info("Working in subscription: %s", emphasised(subscription_name))

    # Create the backend resource group
    logging.info("Ensuring existence of resource group: %s", emphasised(args.resource_group))
    resource_mgmt_client = get_client_from_cli_profile(ResourceManagementClient)
    resource_mgmt_client.resource_groups.create_or_update(args.resource_group, {"location": args.location})

    # Check whether there is already a storage account and generate one if not
    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_account_name = None
    for storage_account in storage_mgmt_client.storage_accounts.list_by_resource_group(args.resource_group):
        if "terraformstorage" in storage_account.name:
            storage_account_name = storage_account.name
            break
    if storage_account_name:
        logging.info("Found existing storage account named: %s", emphasised(storage_account_name))
    else:
        storage_account_name = generate_new_storage_account(storage_mgmt_client)

    # Get the account key for this storage account
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(args.resource_group, storage_account_name)
    storage_account_key = [k.value for k in storage_key_list.keys if k.key_name == "key1"][0]

    # Create a container
    logging.info("Ensuring existence of storage container: %s", emphasised(args.storage_container_name))
    block_blob_service = BlockBlobService(account_name=storage_account_name, account_key=storage_account_key)
    if not block_blob_service.exists(args.storage_container_name):
        block_blob_service.create_container(args.storage_container_name)

    # Write Terraform configuration
    terraform_config_file_lines = [
        'terraform {',
        '  backend "azurerm" {',
        '    storage_account_name = "{}"'.format(storage_account_name),
        '    container_name       = "{}"'.format(args.storage_container_name),
        '    key                  = "terraform.tfstate"',
        '    access_key           = "{}"'.format(storage_account_key),
        '  }',
        '}'
    ]
        # 'variable "subscription_id" {',
        # '    default = "{}"'.format(subscription_id),
        # '}',
        # 'variable "tenant_id" {',
        # '    default = "{}"'.format(tenant_id),
        # '}',
        # 'variable "location" {',
        # '    default = "{}"'.format(args.location),
        # '}',
        # 'variable "azure_group_id" {',
        # '    default = "{}"'.format(args.azure_group_id),
        # '}',
        # 'variable "diagnostics_storage_uri" {',
        # '    default = "{}"'.format(args.azure_group_id),
        # '}',
    terraform_variables_file_lines = [
        'output "subscription_id" {',
        '    value = "{}"'.format(subscription_id),
        '}',
        'output "tenant_id" {',
        '    value = "{}"'.format(tenant_id),
        '}',
        'output "location" {',
        '    value = "{}"'.format(args.location),
        '}',
        'output "azure_group_id" {',
        '    value = "{}"'.format(args.azure_group_id),
        '}',
        'output "diagnostics_storage_uri" {',
        '    value = "{}"'.format(args.azure_group_id),
        '}',
    ]

    # Write Terraform backend config
    os.makedirs(os.path.join("terraform", "configuration"))
    filepath = os.path.join("terraform", "backend_config.tf")
    logging.info("Writing Terraform backend config to: %s", emphasised(filepath))
    with open(filepath, "w") as f_config:
        for line in terraform_config_file_lines:
            f_config.write(line + "\n")

    # Write Terraform common variables
    filepath = os.path.join("terraform", "configuration", "outputs.tf")
    logging.info("Writing Terraform backend config to: %s", emphasised(filepath))
    with open(filepath, "w") as f_config:
        for line in terraform_variables_file_lines:
            f_config.write(line + "\n")


def get_valid_storage_account_name(storage_mgmt_client):
    """Keep generating storage account names until a valid one is found."""
    while True:
        storage_account_name = "terraformstorage"
        storage_account_name += "".join([random.choice(string.ascii_lowercase + string.digits)
                                         for n in range(24 - len(storage_account_name))])
        if storage_mgmt_client.storage_accounts.check_name_availability(storage_account_name).name_available:
            return storage_account_name


def generate_new_storage_account(storage_mgmt_client):
    """Create a new storage account."""
    storage_account_name = get_valid_storage_account_name(storage_mgmt_client)
    logging.info("Creating new storage account: %s", emphasised(storage_account_name))
    storage_async_operation = storage_mgmt_client.storage_accounts.create(
        args.resource_group,
        storage_account_name,
        StorageAccountCreateParameters(
            sku=Sku(name=SkuName.standard_lrs),
            kind=Kind.storage,
            location=args.location
        )
    )
    # Wait until storage_async_operation has finished before returning
    storage_async_operation.result()
    return storage_account_name


if __name__ == "__main__":
    build_backend()
