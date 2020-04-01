"""
Insert static datasets into the database
"""
import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
import termcolor
import docker
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService
from azure.keyvault import KeyVaultClient
from azure.mgmt.keyvault import KeyVaultManagementClient


def emphasised(text):
    """Emphasise text"""
    return termcolor.colored(text, "cyan")


def get_blob_service(resource_group, storage_container_name):
    """Get a BlockBlobService for a given storage container in a known resource group"""
    logging.info(
        "Retrieving key for storage account: %s", emphasised(storage_container_name)
    )
    storage_mgmt_client = get_client_from_cli_profile(StorageManagementClient)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(
        resource_group, storage_container_name
    )
    storage_account_key = [
        k.value for k in storage_key_list.keys if k.key_name == "key1"
    ][0]
    return BlockBlobService(
        account_name=storage_container_name, account_key=storage_account_key
    )


def download_blobs(blob_service, dataset, target_directory):
    """Download blobs from a container to a target directory"""
    # Get the blob container name
    dataset_to_blob_container = {
        "rectgrid_100": "100mgrid",
        "street_canyon": "canyonslondon",
        "hexgrid": "glahexgrid",
        "london_boundary": "londonboundary",
        "oshighway_roadlink": "oshighwayroadlink",
        "scoot_detector": "scootdetectors",
        "ukmap": "ukmap",
        "urbanvillage": "urbanvillage",
    }
    blob_container = dataset_to_blob_container[dataset]
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
        if target_file[-4:] == ".zip":
            logging.info("Unzipping file")
            with zipfile.ZipFile(target_file, "r") as zip_ref:
                zip_ref.extractall(target_directory)
                os.remove(target_file)
            logging.info("Downloading complete")


def get_key_vault_uri_and_client():
    """Get the key vault and key vault client for Clean Air secrets"""
    # Load key vault
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [
        v
        for v in keyvault_mgmt_client.vaults.list_by_subscription()
        if "cleanair" in v.name
    ][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
    return (vault.properties.vault_uri, keyvault_client)


def build_database_secrets(secret_prefix, secrets_directory, local_secret=None):
    """Build temporary JSON file containing database secrets"""
    # Retrieve secrets from local file
    if local_secret:
        logging.info(
            "Using database information from local file %s",
            emphasised(os.path.basename(local_secret)),
        )
        shutil.copyfile(
            local_secret, os.path.join(secrets_directory, "db_secrets.json")
        )
    # Retrieve secrets from key vault
    else:
        vault_uri, keyvault_client = get_key_vault_uri_and_client()
        db_name = keyvault_client.get_secret(
            vault_uri, "{}-name".format(secret_prefix), ""
        ).value
        db_server_name = keyvault_client.get_secret(
            vault_uri, "{}-server-name".format(secret_prefix), ""
        ).value
        db_admin_username = keyvault_client.get_secret(
            vault_uri, "{}-admin-username".format(secret_prefix), ""
        ).value
        db_admin_password = keyvault_client.get_secret(
            vault_uri, "{}-admin-password".format(secret_prefix), ""
        ).value
        database_secrets = {
            "host": "{}.postgres.database.azure.com".format(db_server_name),
            "port": 5432,
            "db_name": db_name,
            "username": "{}@{}".format(db_admin_username, db_server_name),
            "password": db_admin_password,
            "ssl_mode": "require",
        }
        # Write secrets to a temporary file
        with open(os.path.join(secrets_directory, "db_secrets.json"), "w") as f_secret:
            json.dump(database_secrets, f_secret)


def build_docker_image(image_name, dockerfile):
    """Build a Docker image locally"""
    client = docker.DockerClient()
    container_path = os.path.realpath(
        os.path.join(os.path.dirname(sys.argv[0]), "..", "containers")
    )
    dockerfile_path = os.path.join(container_path, "dockerfiles", dockerfile)
    logging.info("Building Docker image: %s", emphasised(image_name))
    image, _ = client.images.build(
        path=container_path, dockerfile=dockerfile_path, tag=image_name
    )
    return image


def run_container(image_name, verbosity, mounts):
    """Run the job, parsing log messages and re-logging them"""
    client = docker.DockerClient()
    container = client.containers.run(
        image_name,
        verbosity,
        volumes=mounts,
        detach=True,
        remove=True,
        stderr=True,
        stdout=True,
    )
    for line in container.logs(stream=True):
        line = line.decode("utf-8")
        try:
            lvl = [
                l
                for l in ("CRITICAL", "WARNING", "ERROR", "INFO", "DEBUG")
                if l in line.split(":")[2]
            ][0]
        except IndexError:
            lvl = "INFO"
        msg = ":".join(line.split(":")[3:])
        if not msg:
            msg = line
        getattr(logging, lvl.lower())(msg.strip())


def upload_static_data(
    image_name, verbosity, dataset, secrets_directory, data_directory
):
    """Upload static data to the database"""
    # Run docker image to upload the data
    logging.info("Preparing to upload %s data...", emphasised(dataset))

    # List of dataset names inside each directory
    dataset_to_directory = {
        "rectgrid_100": "100m_grid.gpkg",
        "street_canyon": "CanyonsLondon_Erase",
        "hexgrid": "Hex350_grid_GLA",
        "london_boundary": "ESRI",
        "oshighway_roadlink": "RoadLink",
        "scoot_detector": "scoot_detectors",
        "ukmap": "UKMap.gdb",
    }

    # Construct Docker arguments
    local_path = os.path.join(data_directory, dataset_to_directory[dataset])
    remote_path = dataset + ".gdb" if local_path.endswith(".gdb") else dataset
    mounts = {
        secrets_directory: {"bind": "/secrets", "mode": "ro"},
        local_path: {"bind": os.path.join("/data", remote_path), "mode": "ro"},
    }

    # Check that image exists
    client = docker.DockerClient()
    if image_name not in sum([image.tags for image in client.images.list()], []):
        logging.error("Docker image %s could not be found!", emphasised(image_name))
        raise ValueError("Docker image {} could not be found!".format(image_name))

    # Run the job
    run_container(image_name, verbosity, mounts)
    logging.info("Finished uploading %s data", emphasised(dataset))


def main():
    """Insert static datasets into the database"""
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Download static datasets")
    parser.add_argument(
        "-a",
        "--azure-group-id",
        type=str,
        default="35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c",
        help="ID of an Azure group which contains developers. Default is Turing's 'All Users' group.",
    )
    parser.add_argument(
        "-g",
        "--resource-group",
        type=str,
        default="Datasets",
        help="Resource group where the static datasets will be stored",
    )
    parser.add_argument(
        "-s",
        "--storage-container-name",
        type=str,
        default="londonaqdatasets",
        help="Name of the storage container where the Terraform backend will be stored",
    )
    parser.add_argument(
        "-l",
        "--local-secret",
        type=str,
        default=None,
        help="Optionally pass the full path of a database secret file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity by one step for each occurence",
    )
    args = parser.parse_args()

    # Construct verbosity argument
    verbosity = "-" + ("v" * args.verbose) if args.verbose > 0 else ""

    # Set up logging
    logging.basicConfig(
        format=r"%(asctime)s %(levelname)8s: %(message)s",
        datefmt=r"%Y-%m-%d %H:%M:%S",
        level=max(20 - 10 * args.verbose, 10),
    )
    logging.getLogger("adal-python").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)

    # Build local Docker images
    static_image = build_docker_image(
        "static:upload", "process_static_dataset.Dockerfile"
    )

    rectgrid_image = build_docker_image(
        "rectgrid:upload", "process_rectgrid.Dockerfile"
    )

    # List of available datasets
    datasets = [
        "hexgrid",
        "london_boundary",
        "oshighway_roadlink",
        "rectgrid_100",
        "scoot_detector",
        "street_canyon",
        "ukmap",
        "urbanvillage",
    ]

    # Get a block blob service
    block_blob_service = get_blob_service(
        args.resource_group, args.storage_container_name
    )

    # Write the database secrets to a temporary directory
    with tempfile.TemporaryDirectory() as secrets_directory:
        build_database_secrets(
            "cleanair-inputs-db", secrets_directory, args.local_secret
        )

        # Download the static data and add to the database
        for dataset in datasets:
            with tempfile.TemporaryDirectory() as data_directory:
                download_blobs(block_blob_service, dataset, data_directory)
                upload_static_data(
                    static_image.tags[0],
                    verbosity,
                    dataset,
                    secrets_directory,
                    data_directory,
                )

        # Upload the rectgrid to the database
        logging.info("Preparing to upload %s data...", emphasised("rectgrid"))
        run_container(
            rectgrid_image.tags[0],
            verbosity,
            {secrets_directory: {"bind": "/secrets", "mode": "ro"}},
        )


if __name__ == "__main__":
    main()
