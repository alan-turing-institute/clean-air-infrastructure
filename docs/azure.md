# Azure Infrastructure

For this section, you will need an Azure account and be listed as a "contributor" on the Urbanair Azure subscription of the Alan Turing Institute.
Please contact [an active contributor](contributor.md) for more information.

To view our Azure infrastructure, you can visit the [Azure portal](https://portal.azure.com/) and use the search bar to find the `Urbanair` subscription.

***

## Sign into the Azure CLI

You can access features of Azure via the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/).
By [installing the cleanair package](installation.md), the Azure CLI will also be installed.

Now simply login using your Azure account:

```bash
az login
```

### Infrastructure developers

Infrastructure developers should additionally check which Azure subscriptions you have access to by running
```bash
az account list --output table --refresh
```

Then set your default subscription to the Clean Air project (if you cannot see it in the output generated from the last line you do not have access):
```bash
az account set --subscription "CleanAir"
```
