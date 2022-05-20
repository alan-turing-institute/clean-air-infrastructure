"""
Authenticate with Azure and get relevant keys
"""
# pylint: skip-file
import logging
import termcolor
import os
from azure.identity import AzureCliCredential
from azure.keyvault import KeyVaultClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.compute import ComputeManagementClient


def emphasised(text):
    """Emphasise text"""
    return termcolor.colored(text, "cyan")


def get_keys(
    machine, rg_name="RG_CLEANAIR_DATA_COLLECTION", rg_kv="RG_CLEANAIR_INFRASTRUCTURE"
):
    """Retrieve keys needed for GitHub connection"""
    # Construct resource names
    vm_name = "{}-vm".format(machine)
    secret_name = "{}-github-secret".format(machine)

    # Read the SSH key from the deployed machine
    logging.info(
        "Obtaining secret from %s in resource group %s...",
        emphasised(vm_name),
        emphasised(rg_name),
    )
    compute_mgmt_client = ComputeManagementClient(AzureCliCredential())
    remote_cmd = {
        "command_id": "RunShellScript",
        "script": ["cat /home/dockerdaemon/.ssh/id_rsa.pub"],
    }
    poller = compute_mgmt_client.virtual_machines.run_command(
        rg_name, vm_name, remote_cmd
    )
    result = poller.result()  # Blocking till executed
    ssh_key = [l for l in result.value[0].message.split("\n") if "ssh-rsa" in l][0]
    logging.info(
        "... please go to clean-air-infrastructure > Settings > Deploy keys on GitHub"
    )
    logging.info("    ensure that there is a key called %s", emphasised(vm_name))
    logging.info("    ensure it is read-only (ie. do not enable write)")
    logging.info("    its value should be: %s", emphasised(ssh_key))

    # Read the GitHub secret from the keyvault
    keyvault_mgmt_client = KeyVaultManagementClient(AzureCliCredential)
    vault = [
        v
        for v in keyvault_mgmt_client.vaults.list_by_resource_group(rg_kv)
        if "cleanair" in v.name
    ][0]
    keyvault_client = KeyVaultClient(AzureCliCredential)
    github_secret = keyvault_client.get_secret(
        vault.properties.vault_uri, secret_name, ""
    ).value
    webhook_url = "http://{}.uksouth.cloudapp.azure.com/github".format(machine)
    logging.info(
        "... please go to clean-air-infrastructure > Settings > Webhooks on GitHub"
    )
    logging.info(
        "    ensure that there is a webhook called %s", emphasised(webhook_url)
    )
    logging.info(
        "    then change the 'Secret' for this webhook to %s", emphasised(github_secret)
    )


def main():
    """Authenticate with Azure and get relevant keys"""
    # Set up logging
    logging.basicConfig(
        format=r"%(asctime)s %(levelname)8s: %(message)s",
        datefmt=r"%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    logging.getLogger("adal-python").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)

    # Get subscription
    
    # Acquire a credential object using CLI-based authentication.
    credential = AzureCliCredential()
    _, subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    # Obtain the management object for resources.
    subscription_client = SubscriptionClient(credential)
    subscription_name = subscription_client.subscriptions.get(
        subscription_id
    ).display_name
    logging.info("Working in subscription: %s", emphasised(subscription_name))

    # Get keys for all relevant VMs
    get_keys("cleanair-orchestrator")


if __name__ == "__main__":
    main()
