import argparse
import logging
import os
import tempfile
import zipfile
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService
from azure.keyvault import KeyVaultClient
from azure.mgmt.keyvault import KeyVaultManagementClient
import subprocess
import json
import docker as dockerapi

# Set up logging
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


def emphasised(text):
    return termcolor.colored(text, 'green')


def get_blob_service(resource_group, storage_container_name):
    # Get subscription
    _, subscription_id = get_azure_cli_credentials()
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(subscription_id).display_name
    logging.info("Working in subscription: %s", emphasised(subscription_name))

    # Get the account key for this storage account
    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(resource_group, storage_container_name)
    storage_account_key = [k.value for k in storage_key_list.keys if k.key_name == "key1"][0]

    logging.info("Retrieved storage account key for downloading")
    return BlockBlobService(account_name=storage_container_name, account_key=storage_account_key)


def download_blobs(blob_service, blob_container, target_directory):
    """
    Download blobs in a container to a target director

    Arguments:
    blob_service -- An Azure blob storage instance
    blob_container -- Name of the blob container to download files from
    target_directory -- Local directory to download files to
    """
    # Ensure that the target directory exists
    os.makedirs(target_directory, exist_ok=True)
    for blob in blob_service.list_blobs(blob_container):
        # Write the data to a local file
        target_file = os.path.join(target_directory, blob.name)
        logging.info("Downloading: %s from container: %s to: %s",
                     emphasised(blob.name), emphasised(blob_container), emphasised(target_file))
        blob_service.get_blob_to_path(blob_container, blob.name, target_file)
        # Unzip the data
        with zipfile.ZipFile(target_file, "r") as zip_ref:
            zip_ref.extractall(target_directory)
            os.remove(target_file)
        logging.info("Downloading complete")


# def download_static_data(container, target_dir, blob_service):
#     # Containers to download data from
#     containers = ["londonboundary", "ukmap", "oshighwayroadlink", "canyonslondon", "glahexgrid"]

#     # Download blobs
#     for container in containers:
#         download_blobs(blob_service, container, target_dir)

# def build_docker_image(database_secret_prefix):
#     # Build static datasources docker image
#     keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
#     vault = [v for v in keyvault_mgmt_client.vaults.list_by_subscription() if "cleanair" in v.name][0]
#     keyvault_client = get_client_from_cli_profile(KeyVaultClient)
#     # db_server_name = keyvault_client.get_secret(vault.properties.vault_uri, "{}-server-name".format(database_secret_prefix), "").value
#     # db_admin_username = keyvault_client.get_secret(vault.properties.vault_uri, "{}-admin-username".format(database_secret_prefix), "").value
#     # db_admin_password = keyvault_client.get_secret(vault.properties.vault_uri, "{}-admin-password".format(database_secret_prefix), "").value
#     container_registry_login_server = keyvault_client.get_secret(vault.properties.vault_uri, "container-registry-login-server", "").value


#     latest_commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")

#     # print("db_server_name", db_server_name)
#     # print("db_admin_username", db_admin_username)
#     # print("db_admin_password", db_admin_password)
#     print("latest_commit_hash", latest_commit_hash, type(latest_commit_hash))
#     # acr_server =

#     # cmd = ["docker", "build", "-t", "{}/static:{}".format(container_registry_login_server, latest_commit_hash), "-f", "docker/dockerfiles/upload_static_dataset.Dockerfile", "docker/."]
#     # print(cmd)
#     # print(" ".join(cmd))

#     # cmd = ["docker", "push", "{}/static:{}".format(container_registry_login_server, latest_commit_hash)]
#     # print(cmd)
#     # print(" ".join(cmd))

#     # client = dockerapi.from_env()

#     # client.images.build(path="docker/dockerfiles/upload_static_dataset.Dockerfile", tag="{}/static:{}".format(container_registry_login_server, latest_commit_hash))

#     # docker build -t cleanair_upload_static_dataset:latest \
# #     -f docker/dockerfiles/upload_static_dataset.Dockerfile \
# #     docker

def get_key_vault_and_client():
    # Load key vault
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [v for v in keyvault_mgmt_client.vaults.list_by_subscription() if "cleanair" in v.name][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
    return (vault, keyvault_client)

def store_database_secrets(database_secret_prefix, secrets_directory):
    # Load key vault
    # keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    # vault = [v for v in keyvault_mgmt_client.vaults.list_by_subscription() if "cleanair" in v.name][0]
    # keyvault_client = get_client_from_cli_profile(KeyVaultClient)
    vault, keyvault_client = get_key_vault_and_client()
    # Retrieve secrets from key vault
    db_name = keyvault_client.get_secret(vault.properties.vault_uri, "{}-name".format(database_secret_prefix), "").value
    db_server_name = keyvault_client.get_secret(vault.properties.vault_uri, "{}-server-name".format(database_secret_prefix), "").value
    db_admin_username = keyvault_client.get_secret(vault.properties.vault_uri, "{}-admin-username".format(database_secret_prefix), "").value
    db_admin_password = keyvault_client.get_secret(vault.properties.vault_uri, "{}-admin-password".format(database_secret_prefix), "").value
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
    # Run docker image to upload the data
    logging.info("Preparing to upload {} data...".format(dataset))

    # List of dataset names inside each directory
    dataset_to_directory = {
        "canyonslondon": "CanyonsLondon_Erase",
        "glahexgrid": "Hex350_grid_GLA",
        "londonboundary": "ESRI",
        "oshighwayroadlink": "RoadLink",
        "ukmap": "UKMap.gdb",
    }

    # Get registry details
    vault, keyvault_client = get_key_vault_and_client()
    registry_login_server = keyvault_client.get_secret(vault.properties.vault_uri, "container-registry-login-server", "").value
    registry_admin_username = keyvault_client.get_secret(vault.properties.vault_uri, "container-registry-admin-username", "").value
    registry_admin_password = keyvault_client.get_secret(vault.properties.vault_uri, "container-registry-admin-password", "").value

    # Get latest commit hash
    latest_commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")

    # Local volumes to mount
    local_data = os.path.join(data_directory, dataset_to_directory[dataset])
    mounted_data = os.path.join("/data", dataset)

    # Log in to the registry and run the job
    client = dockerapi.DockerClient()
    client.login(username=registry_admin_username, password=registry_admin_password, registry=registry_login_server)
    container = client.containers.run("{}/static:{}".format(registry_login_server, latest_commit_hash), volumes={secrets_directory: {'bind': '/secrets', 'mode': 'ro'}, local_data: {'bind': mounted_data, 'mode': 'ro'}}, stdout=True, stderr=True, detach=True)

    # Parse log messages and re-log them
    for line in container.logs(stream=True):
        line = line.decode("utf-8")
        lvl = [l for l in ("CRITICAL", "WARNING", "ERROR", "INFO", "DEBUG") if l in line.split(":")[2]][0]
        msg = ":".join(line.split(":")[3:]).strip()
        getattr(logging, lvl.lower())(msg)


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

    # build_docker_image("cleanair-inputs-db") #-server-name", "cleanair-inputs-db-admin-password", "cleanair-inputs-db-admin-name")

    # Get a block blob service
    block_blob_service = get_blob_service(args.resource_group, args.storage_container_name)

    # db_secrets = get_database_secrets("cleanair-inputs-db")

    # Write the database secrets to a temporary directory
    with tempfile.TemporaryDirectory() as secrets_directory:
        store_database_secrets("cleanair-inputs-db", secrets_directory)

        # Download the static data
        for dataset in datasets:
            with tempfile.TemporaryDirectory() as data_directory:
                download_blobs(block_blob_service, dataset, data_directory)
                upload_static_data(dataset, secrets_directory, data_directory)


if __name__ == '__main__':
    main()


    # tmp_directory = tempfile.TemporaryDirectory()

    # print("PARENT_DIR", tmp_directory)


#     download_static_data(tmp_directory, block_blob_service)

#     # Build the docker image
#    # Run ogr2ogr
#         subprocess.run(["ogr2ogr", "-overwrite", "-progress",
#                         "-f", "PostgreSQL", "PG:{}".format(connection_string), "/data/{}".format(self.static_filename),
#                         "--config", "PG_USE_COPY", "YES",
#                         "-t_srs", "EPSG:4326"] + extra_args)

