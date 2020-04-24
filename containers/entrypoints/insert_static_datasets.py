"""
Insert static datasets into the database
"""
# import argparse
# import json
import logging
import os
# import shutil
# import sys
import tempfile
import zipfile
import termcolor
# import docker
# from azure.common.client_factory import get_client_from_cli_profile
# from azure.mgmt.storage import StorageManagementClient
# from azure.storage.blob import BlockBlobService
# from azure.keyvault import KeyVaultClient
# from azure.mgmt.keyvault import KeyVaultManagementClient

from cleanair.parsers import DatabaseSetupParser
from cleanair.inputs import StaticWriter
from azure.storage.blob import BlobServiceClient

DATASETS = {
                "street_canyon": {"blob_container": "canyonslondon",
                                  "schema": "static_data", 
                                  "table": "street_canyon"},
                "hexgrid": {"blob_container": "glahexgrid", 
                            "schema": "interest_points", 
                            "table": "hexgrid"},
                "london_boundary": {"blob_container": "londonboundary", 
                                    "schema": "static_data", 
                                    "table": "london_boundary"},
                "oshighway_roadlink": {"blob_container": "oshighwayroadlink", 
                                       "schema": "static_data", 
                                       "table": "oshighway_roadlink"},
                "scoot_detector": {"blob_container": "scootdetectors", 
                                    "schema": "interest_points", 
                                    "table": "scoot_detector"},
                "ukmap": {"blob_container": "ukmap", 
                          "schema": "static_data", 
                          "table": "ukmap"},
                "urban_village": {"blob_container": "urbanvilliage", 
                                  "schema": "interest_points", 
                                  "table": "urbanvilliage"},
}

def emphasised(text):
    """Emphasise text"""
    return termcolor.colored(text, "cyan")

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
        "urban_village": "urban_villages",
    }

    # Construct Docker arguments
    local_path = os.path.join(data_directory, dataset_to_directory[dataset])
    remote_path = dataset + ".gdb" if local_path.endswith(".gdb") else dataset
    
    print(local_path)
    print(remote_path)
    quit()
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



def download_blobs(blob_service, blob_container_name, target_directory):
    """Download blobs from a container to a target directory"""
    # Get the blob container name
    
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

        with open(target_file, 'wb') as my_blob:
            blob_data = blob_container_client.download_blob(blob.name)
            blob_data.readinto(my_blob)

        # Unzip the data
        if target_file[-4:] == ".zip":
            logging.info("Unzipping file")
            with zipfile.ZipFile(target_file, "r") as zip_ref:
                zip_ref.extractall(target_directory)
                os.remove(target_file)
            logging.info("Downloading complete")
        else:
            raise Exception("The blob is not a .zip file")

        


        # blob_data.readinto(target_file)

    # for blob in blob_service.list_blobs(blob_container):
    #     # Write the data to a local file
    #     logging.info("Downloading: %s", emphasised(blob.name))
    #     logging.info("... from container: %s", emphasised(blob_container))
    #     logging.info("... to: %s", emphasised(target_directory))

    #     target_file = os.path.join(target_directory, blob.name)
    #     blob_service.get_blob_to_path(blob_container, blob.name, target_file)

  
def main():

    parser = DatabaseSetupParser(DATASETS)
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        format=r"%(asctime)s %(levelname)8s: %(message)s",
        datefmt=r"%Y-%m-%d %H:%M:%S",
        level=max(20 - 10 * args.verbose, 10),
    )
    logging.getLogger("azure").setLevel(logging.WARNING)

    blob_service_client = BlobServiceClient(account_url=args.account_url, credential=args.sas_token)
    
    # Download the static data and add to the database
    for dataset in DATASETS.keys():
        with tempfile.TemporaryDirectory() as data_directory:

            # Initialise the writer first to check database connection
            static_writer = StaticWriter(data_directory, DATASETS[dataset]['schema'], DATASETS[dataset]['table'], secretfile = args.secretfile)

            download_blobs(blob_service_client, DATASETS[dataset]['blob_container'], data_directory)


            # print(os.listdir(data_directory))
            static_writer.update_remote_tables()
            quit()

if __name__ == "__main__":
    main()