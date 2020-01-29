"""
Setup initial Azure infrastructure used by Terraform
"""
import argparse
import logging
import os
import random
import string
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
from azure.storage.blob import BlockBlobService


def build_backend(args):
    """Build the Terraform backend"""
    subscription_id, tenant_id = get_azure_credentials()

    # Create the backend resource group
    logging.info(
        "Ensuring existence of resource group: %s", emphasised(args.resource_group)
    )
    resource_mgmt_client = get_client_from_cli_profile(ResourceManagementClient)
    resource_mgmt_client.resource_groups.create_or_update(
        args.resource_group, {"location": args.location}
    )

    # Check whether there is already a storage account and generate one if not
    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_account_name = None
    for storage_account in storage_mgmt_client.storage_accounts.list_by_resource_group(
        args.resource_group
    ):
        if "terraformstorage" in storage_account.name:
            storage_account_name = storage_account.name
            break
    if storage_account_name:
        logging.info(
            "Found existing storage account named: %s", emphasised(storage_account_name)
        )
    else:
        storage_account_name = generate_new_storage_account(
            storage_mgmt_client, args.resource_group, args.location
        )

    # Get the account key for this storage account
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(
        args.resource_group, storage_account_name
    )
    storage_account_key = [
        k.value for k in storage_key_list.keys if k.key_name == "key1"
    ][0]

    # Create a container
    logging.info(
        "Ensuring existence of storage container: %s",
        emphasised(args.storage_container_name),
    )
    block_blob_service = BlockBlobService(
        account_name=storage_account_name, account_key=storage_account_key
    )
    if not block_blob_service.exists(args.storage_container_name):
        block_blob_service.create_container(args.storage_container_name)

    # Create directories for configuration files
    os.makedirs(os.path.join("terraform", "configuration"), exist_ok=True)

    # Write Terraform backend configuration
    write_backend_configuration(
        storage_account_name, args.storage_container_name, storage_account_key
    )

    # Ensure that key vault exists for storing secrets
    vault = ensure_keyvault(
        args.resource_group, args.location, tenant_id, args.azure_group_id
    )

    # Ensure all secrets are recorded in the key vault
    secrets = {
        "aws_key_id": args.aws_key_id,
        "aws_key": args.aws_key,
        "azure_group_id": args.azure_group_id,
        "azure_sp_id": args.azure_sp_id,
        "azure_sp_name": args.azure_sp_name,
        "azure_sp_password": args.azure_sp_password,
        "location": args.location,
        "subscription_id": subscription_id,
        "tenant_id": tenant_id,
    }
    record_all_secrets(vault.properties.vault_uri, vault.name, secrets)


def emphasised(text):
    """Emphasise text"""
    return termcolor.colored(text, "cyan")


def ensure_keyvault(resource_group, location, tenant_id, azure_group_id):
    """Ensure that a key vault exists for storing secrets"""
    key_vault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    return key_vault_mgmt_client.vaults.create_or_update(
        resource_group,
        "terraform-configuration",
        {
            "location": location,
            "properties": {
                "sku": {"name": "standard"},
                "tenant_id": tenant_id,
                "access_policies": [
                    {
                        "tenant_id": tenant_id,
                        "object_id": azure_group_id,
                        "permissions": {"secrets": ["all"]},
                    }
                ],
            },
        },
    ).result()


def generate_new_storage_account(storage_mgmt_client, resource_group, location):
    """Create a new storage account."""
    storage_account_name = get_valid_storage_account_name(storage_mgmt_client)
    logging.info("Creating new storage account: %s", emphasised(storage_account_name))
    storage_async_operation = storage_mgmt_client.storage_accounts.create(
        resource_group,
        storage_account_name,
        StorageAccountCreateParameters(
            sku=Sku(name=SkuName.standard_lrs), kind=Kind.storage, location=location
        ),
    )
    # Wait until storage_async_operation has finished before returning
    storage_async_operation.result()
    return storage_account_name


def get_azure_credentials():
    """Get subscription and tenant IDs"""
    _, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(
        subscription_id
    ).display_name
    logging.info("Working in subscription: %s", emphasised(subscription_name))
    return (subscription_id, tenant_id)


def get_valid_storage_account_name(storage_mgmt_client):
    """Keep generating storage account names until a valid one is found."""
    while True:
        storage_account_name = "terraformstorage"
        storage_account_name += "".join(
            [
                random.choice(string.ascii_lowercase + string.digits)
                for n in range(24 - len(storage_account_name))
            ]
        )
        if storage_mgmt_client.storage_accounts.check_name_availability(
            storage_account_name
        ).name_available:
            return storage_account_name


def record_all_secrets(vault_uri, vault_name, secrets):
    """Ensure secrets are recorded in the key"""
    # Write secrets to the key vault
    kv_client = get_client_from_cli_profile(KeyVaultClient)
    logging.info("Ensuring secrets are in key vault: %s", emphasised(vault_name))
    available_secrets = [
        s.id.split("/")[-1] for s in kv_client.get_secrets(vault_uri)
    ]

    # Add secrets unless they are already in the vault
    # AWS key
    if secrets["aws_key"]:
        if "scoot-aws-key" in available_secrets:
            kv_aws_key = kv_client.get_secret(vault_uri, "scoot-aws-key", "").value
            if kv_aws_key != secrets["aws_key"]:
                logging.warning("AWS key from key vault does not match user-provided version!")
        else:
            kv_client.set_secret(vault_uri, "scoot-aws-key", secrets["aws_key"])
    else:
        if "scoot-aws-key" in available_secrets:
            logging.info("AWS key found in existing key vault: %s", emphasised(vault_name))
        else:
            logging.warning("No AWS key was provided as an argument and there is not one saved in the key vault!")
    # AWS key ID
    if secrets["aws_key_id"]:
        if "scoot-aws-key-id" in available_secrets:
            kv_aws_key_id = kv_client.get_secret(vault_uri, "scoot-aws-key-id", "").value
            if kv_aws_key_id != secrets["aws_key_id"]:
                logging.warning("AWS key ID from key vault does not match user-provided version!")
        else:
            kv_client.set_secret(vault_uri, "scoot-aws-key-id", secrets["aws_key_id"])
    else:
        if "scoot-aws-key-id" in available_secrets:
            logging.info("AWS key ID found in existing key vault: %s", emphasised(vault_name))
        else:
            logging.warning("No AWS key ID was provided as an argument and there is not one saved in the key vault!")
    # Subscription ID
    if "subscription-id" in available_secrets:
        kv_subscription_id = kv_client.get_secret(vault_uri, "subscription-id", "").value
        if kv_subscription_id != secrets["subscription_id"]:
            logging.warning(
                "Updating subscription ID in key vault to %s",
                emphasised(secrets["subscription_id"]),
            )
            kv_client.set_secret(vault_uri, "subscription-id", secrets["subscription_id"])
    else:
        kv_client.set_secret(vault_uri, "subscription-id", secrets["subscription_id"])
    # Generated secrets
    if "tenant-id" not in available_secrets:
        kv_client.set_secret(vault_uri, "tenant-id", secrets["tenant_id"])
    # User-provided secrets
    if "azure-group-id" not in available_secrets:
        if not secrets["azure_group_id"]:
            raise ValueError("Please provide a value for '--azure-group-id'")
        kv_client.set_secret(vault_uri, "azure-group-id", secrets["azure_group_id"])
    if "azure-service-principal-name" not in available_secrets:
        if not secrets["azure_sp_name"]:
            raise ValueError("Please provide a value for '--azure-sp-name'")
        kv_client.set_secret(vault_uri, "azure-service-principal-name", secrets["azure_sp_name"])
    if "azure-service-principal-id" not in available_secrets:
        if not secrets["azure_sp_id"]:
            raise ValueError("Please provide a value for '--azure-sp-id'")
        kv_client.set_secret(vault_uri, "azure-service-principal-id", secrets["azure_sp_id"])
    if "azure-service-principal-password" not in available_secrets:
        if not secrets["azure_sp_password"]:
            raise ValueError("Please provide a value for '--azure-sp-password'")
        kv_client.set_secret(vault_uri, "azure-service-principal-password", secrets["azure_sp_password"])
    if "location" not in available_secrets:
        if not secrets["location"]:
            raise ValueError("Please provide a value for '--location'")
        kv_client.set_secret(vault_uri, "location", secrets["location"])


def write_backend_configuration(
    storage_account_name, storage_container_name, storage_account_key
):
    """Write Terraform backend configuration"""
    terraform_config_file_lines = [
        "terraform {",
        '  backend "azurerm" {',
        '    storage_account_name = "{}"'.format(storage_account_name),
        '    container_name       = "{}"'.format(storage_container_name),
        '    key                  = "terraform.tfstate"',
        '    access_key           = "{}"'.format(storage_account_key),
        "  }",
        "}",
    ]
    filepath = os.path.join("terraform", "backend_config.tf")
    logging.info("Writing Terraform backend config to: %s", emphasised(filepath))
    with open(filepath, "w") as f_config:
        for line in terraform_config_file_lines:
            f_config.write(line + "\n")


def main():
    """Setup initial Azure infrastructure used by Terraform"""
    # Set up logging
    logging.basicConfig(
        format=r"%(asctime)s %(levelname)8s: %(message)s",
        datefmt=r"%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    logging.getLogger("adal-python").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Initialise the Azure infrastructure needed by Terraform"
    )
    parser.add_argument(
        "-i",
        "--aws-key-id",
        type=str,
        default=None,
        help="AWS key ID for accessing TfL SCOOT data.",
    )
    parser.add_argument(
        "-k",
        "--aws-key",
        type=str,
        default=None,
        help="AWS key for accessing TfL SCOOT data.",
    )
    parser.add_argument(
        "-a",
        "--azure-group-id",
        type=str,
        default="35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c",
        help="ID of an Azure group containing all developers. Default is Turing's 'All Users' group.",
    )
    parser.add_argument(
        "-n",
        "--azure-sp-name",
        type=str,
        default="CleanAir",
        help="Name of an Azure service principal that has Contributor permissions on the subscription.",
    )
    parser.add_argument(
        "-s",
        "--azure-sp-id",
        type=str,
        help="App ID for the Azure service principal named above.",
    )
    parser.add_argument(
        "-p",
        "--azure-sp-password",
        type=str,
        help="Password for the Azure service principal named above.",
    )
    parser.add_argument(
        "-l",
        "--location",
        type=str,
        default="uksouth",
        help="Azure datacentre where the Terraform backend will be stored",
    )
    parser.add_argument(
        "-g",
        "--resource-group",
        type=str,
        default="RG_TERRAFORM_BACKEND",
        help="Resource group where the Terraform backend will be stored",
    )
    parser.add_argument(
        "--storage-container-name",
        type=str,
        default="terraformbackend",
        help="Name of the storage container where the Terraform backend will be stored",
    )

    # Build the backend
    build_backend(parser.parse_args())


if __name__ == "__main__":
    main()
