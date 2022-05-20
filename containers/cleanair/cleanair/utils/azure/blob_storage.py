"""Util functions for interacting with Azure blob storage"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import os

from azure.identity import AzureCliCredential
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import (
    BlobServiceClient,
    generate_account_sas,
    ResourceTypes,
    AccountSasPermissions,
    BlobProperties,
)


def generate_sas_token(
    resource_group: str,
    storage_account_name: str,
    storage_account_key: str = None,
    days: int = 1,
    hours: int = 0,
    permit_write: Optional[bool] = False,
):
    """Generate a SAS token when logged in using az login

    Args:
        resource_group: The Azure Resource group
        storage_account_name: The name of the storage account
        storage_account_key: Optionally give the key, if not given, it will be loaded from az cli profile
        days: Number of days until SAS token expires. Shorter is better
        hours: Number of hours until SAS token expires. Shorter is better
    """
    if not storage_account_key:
        subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
        storage_mgmt_client = StorageManagementClient(AzureCliCredential(), subscription_id)
        storage_key_list = storage_mgmt_client.storage_accounts.list_keys(
            resource_group, storage_account_name,
        )
        storage_account_key = [
            k.value for k in storage_key_list.keys if k.key_name == "key1"
        ][0]

    return "?" + generate_account_sas(
        storage_account_name,
        account_key=storage_account_key,
        resource_types=ResourceTypes(service=True, container=True, object=True),
        permission=AccountSasPermissions(read=True, list=True, write=permit_write),
        expiry=datetime.utcnow() + timedelta(days=days, hours=hours),
    )


def download_blob(
    storage_container_name: str,
    blob_name: str,
    account_url: str,
    target_file: str,
    sas_token: str = None,
) -> None:
    """Download a blob from a storge container

    Args:
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
    storage_container_name: str,
    blob_name: str,
    account_url: str,
    source_file: str,
    sas_token: str = None,
) -> None:
    """Upload a file as a blob to a storge container

    Args:
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
        blob_container_client.upload_blob(name=blob_name, data=data)


def list_blobs(
    storage_container_name: str,
    account_url: str,
    sas_token: str = None,
    start: datetime = None,
    end: datetime = None,
    name_starts_with: str = None,
) -> List[BlobProperties]:
    """List the blobs in a given storage container"""
    blob_service_client = BlobServiceClient(
        account_url=account_url, credential=sas_token
    )

    blob_container_client = blob_service_client.get_container_client(
        storage_container_name
    )

    blobs = list(blob_container_client.list_blobs(name_starts_with=name_starts_with))

    if start:
        start = start.replace(tzinfo=timezone.utc)
        blobs = [blob for blob in blobs if blob.creation_time >= start]
    if end:
        end = end.replace(tzinfo=timezone.utc)
        blobs = [blob for blob in blobs if blob.creation_time <= end]

    return blobs


if __name__ == "__main__":
    SAS_TOKEN = generate_sas_token(
        resource_group="Datasets", storage_account_name="londonaqdatasets",
    )

    download_blob(
        storage_container_name="glahexgrid",
        blob_name="Hex350_grid_GLA.zip",
        account_url="https://londonaqdatasets.blob.core.windows.net",
        target_file="test.txt",
        sas_token=SAS_TOKEN,
    )
