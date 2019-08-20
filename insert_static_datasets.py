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

    logging.info("Downloading using storage account key")
    return BlockBlobService(account_name=storage_container_name, account_key=storage_account_key)


def download_blobs(blob_service, blob_container, target_directory):
    """
    Download blobs in a container to a target director

    Arguments:
    block_bloc_servce -- An Azure blob storage instance
    blob_container -- Name of the blob container to download files from
    target_directory -- Local directory to download files to
    """

    generator = blob_service.list_blobs(blob_container)
    os.makedirs(target_directory, exist_ok=True)

    for blob in generator:
        target_file = os.path.join(target_directory, blob.name)
        logging.info("Downloading: %s from container: %s to location: %s",
                     emphasised(blob.name), emphasised(blob_container), emphasised(target_file))
        blob_service.get_blob_to_path(blob_container, blob.name, target_file)

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

def store_database_secrets(database_secret_prefix, secrets_directory):
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [v for v in keyvault_mgmt_client.vaults.list_by_subscription() if "cleanair" in v.name][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
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
    print(dataset, data_directory)
    # # # Insert street canyons
    # echo "Now working on Street Canyons data..."
    # docker run -it \
    #     -v $db_secret_path:/secrets/ \
    #     -v $(realpath static_data_local/CanyonsLondon_Erase):/data/Canyons \
    #     cleanair_upload_static_dataset:latest

    # datafiles = {
    #     "canyonslondon": "CanyonsLondon_Erase",
    #     "RoadLink": "RoadLink",
    #     "RoadLink": "RoadLink",
    # }


    cmd = ["docker", "run", "-it", "-v", "{}:/secrets".format(secrets_directory), "-v", "{}:/data".format(data_directory)]
    print(cmd)


def main():
#     # Get the scipts directory
#     PARENT_DIR = os.path.dirname(os.path.realpath(__file__))

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
    datasets = ["londonboundary", "ukmap", "oshighwayroadlink", "canyonslondon", "glahexgrid"]

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

