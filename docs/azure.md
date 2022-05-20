# Azure Infrastructure

For this section, you will need an Azure account and be listed as a "contributor" on the Urbanair Azure subscription of the Alan Turing Institute.
Please contact [an active contributor](contributor.md) for more information.

To view our Azure infrastructure, you can visit the [Azure portal](https://portal.azure.com/) and use the search bar to find the `Urbanair` subscription.

***

## Sign into the Azure CLI

You can access features of Azure via the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/).
By [installing the cleanair package](installation.md), the Azure CLI should also be installed.

Incase of problems, try installing `azure-cli` with pip (you may bump into dependency conflicts with `cleanair`, but these can usually be safely ignored).

```bash
pip install azure-cli
```

Now simply login using your Azure account:

```bash
az login
```

> If no subscriptions appear and the Azure CLI complains about 2-factor authentication, then visit the [Azure portal](https://portal.azure.com/) and ensure 2-factor authentication is enabled on your Azure account.

### Infrastructure developers

Infrastructure developers should additionally check which Azure subscriptions you have access to by running
```bash
az account list --output table --refresh
```

Then set your default subscription to the Clean Air project (if you cannot see it in the output generated from the last line you do not have access):
```bash
az account set --subscription "Urbanair"
```
