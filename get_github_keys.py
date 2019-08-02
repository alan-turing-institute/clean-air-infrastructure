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
logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s",
                    datefmt=r"%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("adal-python").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


def emphasised(text):
    return termcolor.colored(text, 'green')


def get_keys(datasource, rg_name="RG_CLEANAIR_DATASOURCES", rg_kv="RG_CLEANAIR_INFRASTRUCTURE"):
    # Construct resource names
    vm_name = "{}-VM".format(datasource.upper())
    secret_name = "{}-vm-github-secret".format(datasource)

    # Read the SSH key from the deployed machine
    logging.info("Obtaining secret from %s in resource group %s...", emphasised(vm_name), emphasised(rg_name))
    compute_mgmt_client = get_client_from_cli_profile(ComputeManagementClient)
    remote_cmd = {"command_id": "RunShellScript", "script": ["cat /home/{}daemon/.ssh/id_rsa.pub".format(datasource)]}
    poller = compute_mgmt_client.virtual_machines.run_command(rg_name, vm_name, remote_cmd)
    result = poller.result()  # Blocking till executed
    ssh_key = [l for l in result.value[0].message.split("\n") if "ssh-rsa" in l][0]
    key_name = emphasised('{}-cleanair'.format(datasource))
    logging.info("... please go to clean-air-infrastructure > Settings > Deploy keys on GitHub")
    logging.info("    ensure that there is a key called %s", key_name)
    logging.info("    ensure it is read-only (ie. do not enable write)")
    logging.info("    its value should be: %s", emphasised(ssh_key))

    # Read the GitHub secret from the keyvault
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [v for v in keyvault_mgmt_client.vaults.list_by_resource_group(rg_kv) if "kvcleanair" in v.name][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
    github_secret = keyvault_client.get_secret(vault.properties.vault_uri, secret_name, "").value
    webhook_url = "http://cleanair-{}.uksouth.cloudapp.azure.com/github".format(datasource)
    logging.info("... please go to clean-air-infrastructure > Settings > Webhooks on GitHub")
    logging.info("    ensure that there is a webhook called %s", emphasised(webhook_url))
    logging.info("    then change the 'Secret' for this webhook to %s", emphasised(github_secret))


if __name__ == "__main__":
    # Get subscription
    _, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(subscription_id).display_name
    logging.info("Working in subscription: %s", emphasised(subscription_name))

    # Get keys for the different datasources
    get_keys("aqn")
    get_keys("laqn")
