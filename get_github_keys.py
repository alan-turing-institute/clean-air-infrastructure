#! /usr/bin/env python
# import argparse
import logging
# import os
# import random
# import string
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
# from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.compute import ComputeManagementClient
# from azure.mgmt.storage import StorageManagementClient
# from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
# from azure.storage.blob import BlockBlobService


# Set up logging
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)

# # Read command line arguments
# parser = argparse.ArgumentParser(description='Initialise the Azure infrastructure needed by Terraform')
# parser.add_argument("-g", "--resource-group", type=str, default="RG_TERRAFORM_BACKEND", help="Resource group where the Terraform backend will be stored")
# parser.add_argument("-l", "--location", type=str, default="uksouth", help="Azure datacentre where the Terraform backend will be stored")
# parser.add_argument("-s", "--storage-container-name", type=str, default="terraformbackend", help="Name of the storage container where the Terraform backend will be stored")
# parser.add_argument("-a", "--azure-group-id", type=str, default="35cf3fea-9d3c-4a60-bd00-2c2cd78fbd4c", help="ID of an Azure group which contains all project developers. Default is Turing's 'All Users' group.")
# args = parser.parse_args()

def emphasised(text):
    return termcolor.colored(text, 'green')

def get_keys(vm_name, rg_name):
    # Get subscription
    _, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(subscription_id).display_name
    logging.info("Working in subscription: {}".format(emphasised(subscription_name)))

    # Read the SSH key from the deployed machine
    logging.info("Obtaining secret from {} in resource group {}...".format(emphasised(vm_name), emphasised(rg_name)))
    compute_mgmt_client = get_client_from_cli_profile(ComputeManagementClient)
    poller = compute_mgmt_client.virtual_machines.run_command(rg_name, vm_name, {"command_id": "RunShellScript", "script": ["cat /home/laqndaemon/.ssh/id_rsa.pub"]})
    result = poller.result()  # Blocking till executed
    cmd_output = result.value[0].message
    ssh_key = [l for l in cmd_output.split("\n") if "ssh-rsa" in l][0]
    logging.info("... please add the following key to the 'Deploy keys' section on github (under clean-air-infrastructure > Settings > Deploy keys)")
    logging.info(emphasised(ssh_key))

if __name__ == "__main__":
    get_keys("LAQN-VM", "RG_CLEANAIR_DATASOURCES")
