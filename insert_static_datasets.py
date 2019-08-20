"""
Insert static datasets into the database
"""
import argparse
import json
import logging
import os
import subprocess
import tempfile
import zipfile
import docker
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService
from azure.keyvault import KeyVaultClient
from azure.mgmt.keyvault import KeyVaultManagementClient


# Set up logging
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


def emphasised(text):
    return termcolor.colored(text, "green")


def get_blob_service(resource_group, storage_container_name):
    """Get a BlockBlobService for a given storage container in a known resource group"""
    logging.info("Retrieving key for storage account: %s", emphasised(storage_container_name))
    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(resource_group, storage_container_name)
    storage_account_key = [k.value for k in storage_key_list.keys if k.key_name == "key1"][0]
    return BlockBlobService(account_name=storage_container_name, account_key=storage_account_key)


def download_blobs(blob_service, blob_container, target_directory):
    """Download blobs from a container to a target directory"""
    # Ensure that the target directory exists
    os.makedirs(target_directory, exist_ok=True)
    for blob in blob_service.list_blobs(blob_container):
        # Write the data to a local file
        logging.info("Downloading: %s", emphasised(blob.name))
        logging.info("... from container: %s", emphasised(blob_container))
        logging.info("... to: %s", emphasised(target_directory))
        target_file = os.path.join(target_directory, blob.name)
        blob_service.get_blob_to_path(blob_container, blob.name, target_file)
        # Unzip the data
        with zipfile.ZipFile(target_file, "r") as zip_ref:
            zip_ref.extractall(target_directory)
            os.remove(target_file)
        logging.info("Downloading complete")


def get_key_vault_uri_and_client():
    """Get the key vault and key vault client for Clean Air secrets"""
    # Load key vault
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [v for v in keyvault_mgmt_client.vaults.list_by_subscription() if "cleanair" in v.name][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
    return (vault.properties.vault_uri, keyvault_client)


def build_database_secrets(secret_prefix, secrets_directory):
    """Build temporary JSON file containing database secrets"""
    # Retrieve secrets from key vault
    vault_uri, keyvault_client = get_key_vault_uri_and_client()
    db_name = keyvault_client.get_secret(vault_uri, "{}-name".format(secret_prefix), "").value
    db_server_name = keyvault_client.get_secret(vault_uri, "{}-server-name".format(secret_prefix), "").value
    db_admin_username = keyvault_client.get_secret(vault_uri, "{}-admin-username".format(secret_prefix), "").value
    db_admin_password = keyvault_client.get_secret(vault_uri, "{}-admin-password".format(secret_prefix), "").value
    database_secrets = {
        "host": "{}.postgres.database.azure.com".format(db_server_name),
        "port": 5432,
        "db_name": db_name,
        "username": "{}@{}".format(db_admin_username, db_server_name),
        "password": db_admin_password,
        "ssl_mode": "require"
    }
    # Write secrets to a temporary file
    with open(os.path.join(secrets_directory, "db_secrets.json"), "w") as f_secret:
        json.dump(database_secrets, f_secret)


def upload_static_data(dataset, secrets_directory, data_directory):
    """Upload static data to the database"""
    # Run docker image to upload the data
    logging.info("Preparing to upload %s data...", emphasised(dataset))

    # List of dataset names inside each directory
    dataset_to_directory = {
        "canyonslondon": "CanyonsLondon_Erase",
        "glahexgrid": "Hex350_grid_GLA",
        "londonboundary": "ESRI",
        "oshighwayroadlink": "RoadLink",
        "ukmap": "UKMap.gdb",
    }

    # Get registry details
    vault_uri, keyvault_client = get_key_vault_uri_and_client()
    registry_login_server = keyvault_client.get_secret(vault_uri, "container-registry-login-server", "").value
    registry_admin_username = keyvault_client.get_secret(vault_uri, "container-registry-admin-username", "").value
    registry_admin_password = keyvault_client.get_secret(vault_uri, "container-registry-admin-password", "").value

    # Get latest commit hash
    latest_commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")

    # Log in to the registry
    client = docker.DockerClient()
    client.login(username=registry_admin_username, password=registry_admin_password, registry=registry_login_server)

    # Construct Docker arguments
    image = "{}/static:{}".format(registry_login_server, latest_commit_hash)
    local_data = os.path.join(data_directory, dataset_to_directory[dataset])
    mounts = {
        secrets_directory: {"bind": "/secrets", "mode": "ro"},
        local_data: {"bind": os.path.join("/data", dataset), "mode": "ro"}
    }

    # Run the job, parsing log messages and re-logging them
    container = client.containers.run(image, volumes=mounts, stdout=True, stderr=True, detach=True)
    for line in container.logs(stream=True):
        line = line.decode("utf-8")
        try:
            lvl = [l for l in ("CRITICAL", "WARNING", "ERROR", "INFO", "DEBUG") if l in line.split(":")[2]][0]
        except IndexError:
            lvl = "INFO"
        msg = ":".join(line.split(":")[3:])
        if not msg:
            msg = line
        getattr(logging, lvl.lower())(msg.strip())


def main():
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Download static datasets")
    parser.add_argument("-a", "--azure-group-id", type=str, default="35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c",
                        help="ID of an Azure group which contains developers. Default is Turing's 'All Users' group.")
    parser.add_argument("-g", "--resource-group", type=str, default="Datasets",
                        help="Resource group where the static datasets will be stored")
    parser.add_argument("-s", "--storage-container-name", type=str, default="londonaqdatasets",
                        help="Name of the storage container where the Terraform backend will be stored")
    args = parser.parse_args()

    # List of available datasets
    datasets = ["canyonslondon", "glahexgrid", "londonboundary", "oshighwayroadlink", "ukmap"]

    # Get a block blob service
    block_blob_service = get_blob_service(args.resource_group, args.storage_container_name)

    # Write the database secrets to a temporary directory
    with tempfile.TemporaryDirectory() as secrets_directory:
        build_database_secrets("cleanair-inputs-db", secrets_directory)

        # Download the static data
        for dataset in datasets:
            with tempfile.TemporaryDirectory() as data_directory:
                download_blobs(block_blob_service, dataset, data_directory)
                upload_static_data(dataset, secrets_directory, data_directory)


if __name__ == "__main__":
    main()
