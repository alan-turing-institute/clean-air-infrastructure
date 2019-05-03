#! /usr/bin/env python
import logging
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
from azure.keyvault import KeyVaultClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.compute import ComputeManagementClient

# Set up logging
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s", datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)

def emphasised(text):
    return termcolor.colored(text, 'green')

def get_keys(datasource, rg_name, rg_kv):
    # Construct resource names
    vm_name = "{}-VM".format(datasource.upper())
    secret_name = "{}-vm-github-secret".format(datasource)

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
    key_name = emphasised('{}-cleanair'.format(datasource))
    logging.info("... please add a key called '{}' to the 'Deploy keys' section on github (under clean-air-infrastructure > Settings > Deploy keys)".format(key_name))
    logging.info(emphasised(ssh_key))

    # Read the GitHub secret from the keyvault
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [v for v in keyvault_mgmt_client.vaults.list_by_resource_group(rg_kv) if "kvcleanair" in v.name][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
    github_secret = keyvault_client.get_secret(vault.properties.vault_uri, secret_name, "").value
    webhook_url = emphasised("http://cleanair-{}.uksouth.cloudapp.azure.com/github".format(datasource))
    logging.info("... please add the following secret to the 'Secret' section on github (under clean-air-infrastructure > Settings > Webhooks)")
    logging.info("    the webhook should be called {}".format(webhook_url))
    logging.info(emphasised(github_secret))


if __name__ == "__main__":
    get_keys("laqn", "RG_CLEANAIR_DATASOURCES", "RG_CLEANAIR_INFRASTRUCTURE")
    # get_keys("LAQN-VM", "RG_CLEANAIR_DATASOURCES", "laqn-vm-github-secret", "RG_CLEANAIR_INFRASTRUCTURE")
