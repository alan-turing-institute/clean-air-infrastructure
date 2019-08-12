import argparse
import logging
import os
import zipfile
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService

# Set up logging
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


def emphasised(text):
    return termcolor.colored(text, 'green')


def get_blob_service():

    # Get subscription
    _, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(subscription_id).display_name
    logging.info("Working in subscription: %s, ", emphasised(subscription_name))

    # # Get the account key for this storage account
    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(args.resource_group, args.storage_container_name)
    storage_account_key = [k.value for k in storage_key_list.keys if k.key_name == "key1"][0]

    logging.info("Downloading using storage account key")
    return BlockBlobService(account_name=args.storage_container_name, account_key=storage_account_key)


def create_dir_if_not_exists(d):

    if not os.path.exists(d):
        logging.info("Directory: %s does not exist. Creating directory", emphasised(d))
        os.makedirs(d)


def download_blobs(block_blob_service, blob_container, target_directory):
    """
    Download blobs in a container to a target director

    Arguments:
    block_bloc_servce -- An Azure blob storage instance
    blob_container -- Name of the blob container to download files from
    target_directory -- Local directory to download files to
    """

    generator = block_blob_service.list_blobs(blob_container)
    create_dir_if_not_exists(target_directory)

    for blob in generator:
    
        target_file = os.path.join(target_directory, blob.name)

        # Only download file if it does not exists already
        if not os.path.exists(target_file):
            logging.info("Downloading: %s from container: %s to location: %s", emphasised(blob.name), blob_container, emphasised(target_file))
            block_blob_service.get_blob_to_path(blob_container, blob.name, target_file)

            with zipfile.ZipFile(target_file, "r") as zip_ref:
                zip_ref.extractall(target_directory)
                os.remove(target_file)

            logging.info("Downloading complete")
        else:
            logging.info("Blob: %s already downloaded to location: %s", emphasised(blob.name), emphasised(target_file))


def download_static_data():

    # Get a block blob service class
    block_blob_service = get_blob_service()

    # Containers to download data from
    containers = ["londonboundary", "ukmap", "oshighwayroadlink", "canyonslondon"]

    # Get the directory locations (robust to working directory)
    target_dir = "static_data_local"
    target_dir = os.path.join(PARENT_DIR, target_dir)

    # Download blobs
    for c in containers:

        download_blobs(block_blob_service, c, target_dir)


if __name__ == '__main__':

    # Get the scipts directory
    PARENT_DIR = os.path.dirname(os.path.realpath(__file__))

    # Read command line arguments
    parser = argparse.ArgumentParser(description="Download static datasets")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-a", "--azure-group-id", type=str, default="35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c", help="ID of an Azure group which contains all project developers. Default is Turing's 'All Users' group.")
    parser.add_argument("-g", "--resource-group", type=str, default="Datasets", help="Resource group where the static datasets will be stored")
    parser.add_argument("-s", "--storage-container-name", type=str, default="londonaqdatasets", help="Name of the storage container where the Terraform backend will be stored")

    args = parser.parse_args()

    download_static_data()
