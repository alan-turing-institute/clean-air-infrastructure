"""Util functions for interacting with Azure blob storage"""
from typing import Optional
from datetime import datetime, timedelta
from azure.common.client_factory import get_client_from_cli_profile
from azure.storage.blob import (
    BlobServiceClient,
    generate_account_sas,
    ResourceTypes,
    AccountSasPermissions,
)
from azure.mgmt.storage import StorageManagementClient


def generate_sas_token(
    resource_group: str,
    storage_container_name: str,
    days: int = 1,
    hours: int = 0,
    suffix: Optional[str] = "?",
):
    """Generate a SAS token when logged in using az login
    
    Args:
        resource_group: The Azure Resource group
        storage_container_name: The name of the storage container
        days: Number of days until SAS token expires. Shorter is better
        hours: Number of hours until SAS token expires. Shorter is better
    """

    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(
        resource_group, storage_container_name,
    )
    storage_account_key = [
        k.value for k in storage_key_list.keys if k.key_name == "key1"
    ][0]

    return "?" + generate_account_sas(
        storage_container_name,
        account_key=storage_account_key,
        resource_types=ResourceTypes(service=True, container=True, object=True),
        permission=AccountSasPermissions(read=True, list=True),
        expiry=datetime.utcnow() + timedelta(days=days, hours=hours),
    )


def download_blob(
    resource_group: str,
    storage_container_name: str,
    blob_name: str,
    account_url: str,
    target_file: str,
    sas_token: str = None,
) -> None:
    """Download a blob from a storge container
    
    Args:
        resource_group: The Azure Resource group
        storage_container_name: The name of the storage container
        blob_name: Full path to the blob
        account_url: URL of Azure storage account
        target_file: File to write data to
        sas_token: SAS token for Azure blob storage

    Examples:
        >>> download_blob(
                resource_group="Datasets",
                storage_container_name="glahexgrid",
                blob_name="Hex350_grid_GLA.zip",
                account_url="https://londonaqdatasets.blob.core.windows.net",
                target_file="example.zip",
                sas_token="<sas-token>"
            )
    """

    blob_service_client = BlobServiceClient(
        account_url=account_url, credential=sas_token
    )

    blob_container_client = blob_service_client.get_container_client(
        storage_container_name
    )

    blob_data = blob_container_client.download_blob(blob_name)

    with open(target_file, "wb") as my_blob:
        blob_data.readinto(my_blob)

def upload_blob(
    resource_group: str,
    storage_container_name: str,
    blob_name: str,
    account_url: str,
    source_file: str,
    sas_token: str = None,
) -> None:
    """Upload a file as a blob to a storge container
    
    Args:
        resource_group: The Azure Resource group
        storage_container_name: The name of the storage container
        blob_name: Full path to the blob
        account_url: URL of Azure storage account
        source_file: File to write data to
        sas_token: SAS token for Azure blob storage

    Examples:
        >>> upload_blob(
                resource_group="Datasets",
                storage_container_name="glahexgrid",
                blob_name="Hex350_grid_GLA.zip",
                account_url="https://londonaqdatasets.blob.core.windows.net",
                source_file="example.zip",
                sas_token="<sas-token>"
            )
    """

    blob_service_client = BlobServiceClient(
        account_url=account_url, credential=sas_token
    )

    blob_container_client = blob_service_client.get_container_client(
        storage_container_name
    )

    with open(source_file, "rb") as data:
        blob_client = blob_container_client.upload_blob(name=blob_name, data=data)


        
if __name__ == "__main__":

    SAS_TOKEN = generate_sas_token(
        resource_group="Datasets",
        storage_container_name="londonaqdatasets",
        suffix=None,
    )

    download_blob(
        resource_group="Datasets",
        storage_container_name="glahexgrid",
        blob_name="Hex350_grid_GLA.zip",
        account_url="https://londonaqdatasets.blob.core.windows.net",
        target_file="test.txt",
        sas_token=SAS_TOKEN,
    )
