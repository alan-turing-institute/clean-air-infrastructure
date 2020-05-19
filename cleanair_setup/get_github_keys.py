"""
Authenticate with Azure and get relevant keys
"""
# pylint: skip-file
import logging
import termcolor
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import get_azure_cli_credentials
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
    compute_mgmt_client = get_client_from_cli_profile(ComputeManagementClient)
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
    keyvault_mgmt_client = get_client_from_cli_profile(KeyVaultManagementClient)
    vault = [
        v
        for v in keyvault_mgmt_client.vaults.list_by_resource_group(rg_kv)
        if "cleanair" in v.name
    ][0]
    keyvault_client = get_client_from_cli_profile(KeyVaultClient)
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
    _, subscription_id = get_azure_cli_credentials()
    subscription_client = get_client_from_cli_profile(SubscriptionClient)
    subscription_name = subscription_client.subscriptions.get(
        subscription_id
    ).display_name
    logging.info("Working in subscription: %s", emphasised(subscription_name))

    # Get keys for all relevant VMs
    get_keys("cleanair-orchestrator")


if __name__ == "__main__":
    main()
