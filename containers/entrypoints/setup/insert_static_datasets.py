"""
Insert static datasets into the database
"""
import logging
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta

import termcolor
from azure.identity import AzureCliCredential
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import (
    BlobServiceClient,
    generate_account_sas,
    ResourceTypes,
    AccountSasPermissions,
)
from sqlalchemy import create_engine, inspect
from cleanair.databases import Connector, DBInteractor
from cleanair.inputs import StaticWriter
from cleanair.parsers import DatabaseSetupParser
from cleanair.utils.azure import get_urbanair_az_subscription_id

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


def generate_sas_token(resource_group, storage_container_name, days, hours):
    """Generate a SAS token when logged in using az login"""
    credential = AzureCliCredential()
    subscription_id = get_urbanair_az_subscription_id(credential)
    storage_mgmt_client = StorageManagementClient(credential, subscription_id)
    storage_key_list = storage_mgmt_client.storage_accounts.list_keys(
        resource_group,
        storage_container_name,
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


def configure_database(secretfile):
    "Configure a database, creating all schema and installing extentions"
    db_connection = Connector(secretfile)
    db_connection.ensure_database_exists()
    db_connection.ensure_extensions()


def generate(args):
    """Generate a SAS token"""

    sys.stdout.write(
        generate_sas_token(
            args.resource_group,
            args.storage_container_name,
            args.days,
            args.hours,
        )
    )
    sys.exit(0)


def insert(args):
    """Insert static data into a database"""

    # Check database exists
    configure_database(args.secretfile)

    blob_service_client = BlobServiceClient(
        account_url=args.account_url, credential=args.sas_token
    )
    # engine for querying table names
    engine = create_engine(
        Connector(secretfile=args.secretfile).connection_string, pool_pre_ping=True
    )

    # Download the static data and add to the database
    for dataset in args.datasets:
        with tempfile.TemporaryDirectory() as data_directory:
            existing_table_names = inspect(engine).get_table_names(
                schema=DATASETS[dataset]["schema"]
            )
            # only read from blob storage if the table doesn't exist
            if DATASETS[dataset]["table"] not in existing_table_names:
                target_file = download_blobs(
                    blob_service_client,
                    DATASETS[dataset]["blob_container"],
                    data_directory,
                )
                # Initialise the writer first to check database connection
                static_writer = StaticWriter(
                    target_file,
                    DATASETS[dataset]["schema"],
                    DATASETS[dataset]["table"],
                    secretfile=args.secretfile,
                )
                static_writer.update_remote_tables()

    # Triggers view creation
    DBInteractor(args.secretfile, initialise_tables=True)


def create_parser(datasets):
    """Create parser"""
    parsers = DatabaseSetupParser()

    # Common arguments
    parsers.add_argument(
        "-u",
        "--account_url",
        type=str,
        default="https://londonaqdatasets.blob.core.windows.net",
        help="URL of storage account",
    )

    parsers.add_argument(
        "-c",
        "--storage-container-name",
        type=str,
        default="londonaqdatasets",
        help="Name of the storage container where the Terraform backend will be stored",
    )

    parsers.add_argument(
        "-r",
        "--resource_group",
        type=str,
        default="Datasets",
        help="Resource group where the static datasets will be stored",
    )

    # Subparsers
    subparsers = parsers.add_subparsers(required=True, dest="command")
    parser_generate = subparsers.add_parser(
        "generate",
        help="Generate a SAS Token to download CleanAir static datasets from Azure",
    )
    parser_insert = subparsers.add_parser(
        "insert", help="Insert CleanAir static datasets into a database"
    )

    # Insert parser args
    parser_generate.add_argument(
        "--hours", type=int, default=1, help="Number of hours SAS Token valid for"
    )
    parser_generate.add_argument(
        "--days",
        type=int,
        default=0,
        help="Number of days SAS Token valid for. If used with --hours will be sum of hours and days",
    )

    # Generate parser args
    parser_insert.add_argument(
        "-t",
        "--sas-token",
        type=str,
        help="sas token to access the cleanair datastore container",
    )

    parser_insert.add_argument(
        "-d",
        "--datasets",
        nargs="+",
        type=str,
        choices=datasets,
        default=datasets,
        help="A list of datasets to include",
    )

    # Link to programs
    parser_generate.set_defaults(func=generate)
    parser_insert.set_defaults(func=insert)

    return parsers


def main():
    "Insert static datasets entry point"
    parser = create_parser(datasets=list(DATASETS.keys()))
    args = parser.parse_args()

    # Set logging verbosity
    logging.getLogger("azure").setLevel(logging.WARNING)

    # Execute functions
    args.func(args)


if __name__ == "__main__":
    main()
