"""
Insert static datasets into the database
"""
import logging
import os
import tempfile
import zipfile
import termcolor
from cleanair.parsers import DatabaseSetupParser
from cleanair.inputs import StaticWriter
from azure.storage.blob import (
    BlobServiceClient,
    generate_account_sas,
    ResourceTypes,
    AccountSasPermissions,
)
from azure.mgmt.storage import StorageManagementClient
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.compute import ComputeManagementClient
from datetime import datetime, timedelta

DATASETS = {
    "rectgrid_100": {
        "blob_container": "100mgrid",
        "schema": "interest_points",
        "table": "rectgrid_100",
    },
    "street_canyon": {
        "blob_container": "canyonslondon",
        "schema": "static_data",
        "table": "street_canyon",
    },
    "hexgrid": {
        "blob_container": "glahexgrid",
        "schema": "interest_points",
        "table": "hexgrid",
    },
    "london_boundary": {
        "blob_container": "londonboundary",
        "schema": "static_data",
        "table": "london_boundary",
    },
    "oshighway_roadlink": {
        "blob_container": "oshighwayroadlink",
        "schema": "static_data",
        "table": "oshighway_roadlink",
    },
    "scoot_detector": {
        "blob_container": "scootdetectors",
        "schema": "interest_points",
        "table": "scoot_detector",
    },
    "ukmap": {"blob_container": "ukmap", "schema": "static_data", "table": "ukmap"},
    "urban_village": {
        "blob_container": "urbanvillage",
        "schema": "static_data",
        "table": "urban_village",
    },
}


def emphasised(text):
    """Emphasise text"""
    return termcolor.colored(text, "cyan")


def generate_sas_token(account_url, resource_group, storage_container_name):
    """Generate a SAS token when logged in using az login"""

    client = get_client_from_cli_profile(BlobServiceClient, account_url=account_url)

    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(
        resource_group, storage_container_name,
    )
    storage_account_key = [
        k.value for k in storage_key_list.keys if k.key_name == "key1"
    ][0]

    return generate_account_sas(
         storage_container_name,
        account_key=storage_account_key,
        resource_types=ResourceTypes(object=True),
        permission=AccountSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
    )


def download_blobs(blob_service, blob_container_name, target_directory):
    """Download blobs from a container to a target directory"""

    # Ensure that the target directory exists
    os.makedirs(target_directory, exist_ok=True)

    blob_container_client = blob_service.get_container_client(blob_container_name)

    if len(list(blob_container_client.list_blobs())) != 1:
        raise Exception("Container: {} must have  exactly one blob")

    for blob in blob_container_client.walk_blobs():
        # Write the data to a local file
        logging.info("Downloading: %s", emphasised(blob.name))
        logging.info("... from container: %s", emphasised(blob_container_name))
        logging.info("... to: %s", emphasised(target_directory))

        target_file = os.path.join(target_directory, blob.name)

        with open(target_file, "wb") as my_blob:
            blob_data = blob_container_client.download_blob(blob.name)
            blob_data.readinto(my_blob)

        # Unzip the data
        if target_file[-4:] == ".zip":
            logging.info("Unzipping file")
            with zipfile.ZipFile(target_file, "r") as zip_ref:
                zip_ref.extractall(target_directory)
                os.remove(target_file)
            logging.info("Downloading complete")
            return target_file[:-4]

        return target_file


def main():

    parser = DatabaseSetupParser(list(DATASETS.keys()))
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        format=r"%(asctime)s %(levelname)8s: %(message)s",
        datefmt=r"%Y-%m-%d %H:%M:%S",
        level=max(20 - 10 * args.verbose, 10),
    )
    logging.getLogger("azure").setLevel(logging.WARNING)

    blob_service_client = BlobServiceClient(
        account_url=args.account_url, credential=args.sas_token
    )

    # Download the static data and add to the database
    for dataset in args.datasets:
        with tempfile.TemporaryDirectory() as data_directory:

            target_file = download_blobs(
                blob_service_client, DATASETS[dataset]["blob_container"], data_directory
            )

            # Initialise the writer first to check database connection
            static_writer = StaticWriter(
                target_file,
                DATASETS[dataset]["schema"],
                DATASETS[dataset]["table"],
                secretfile=args.secretfile,
            )
            # print(os.listdir(data_directory))
            static_writer.update_remote_tables()


if __name__ == "__main__":
    # main()

    sas = get_sas()

    print(sas)
