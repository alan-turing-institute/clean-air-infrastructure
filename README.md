# clean-air-infrastructure
Azure Infrastructure for the Clean Air project

## Prerequisites
To run this project you will need an `Azure account` (the cloud-computing platform where the infrastructure is deployed), the `Azure CLI` (for managing your Azure subscriptions), the `Azure Python SDK` (for managing the initial setup) and `Terraform` (for configuring the Azure infrastructure).


### Azure Account
If you do not have an `Azure` account already, please [`follow the procedure here`](https://azure.microsoft.com/en-us/) to get started with an `Azure` subscription.

### Azure CLI
If you have not already installed the command line interface for `Azure`, please [`follow the procedure here`](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) to get started.

### Azure Python SDK
You can install the `Azure` Python SDK with `pip` using:

```
pip install -r requirements
```

### Terraform
The Azure infrastructure is managed with `Terraform`. To get started [download `Terraform` from here](https://www.terraform.io). If using Mac OS, you can instead use `homebrew`:

```
brew install terraform
```

## Getting started
The following steps are needed to setup the Clean Air cloud infrastructure.

### Setup Azure
To start working with `Azure`, you must first login to your account from the terminal:

```
az login
```

Check which `Azure` subscriptions you have access to by running

```
az account list --output table
```

Then set your default subscription to the Clean Air project (if you cannot see it in the output generated from the last line you do not have access):


```
az account set --subscription "Azure project allocation for LRF Clean Air project"
```

### Setup Terraform with Python
You can create the initial `Terraform` configuration by running

```
python initialise_terraform.py
```

This will only need to be run once (by anyone), but it's not a problem if you run it multiple times.





### Setting up the terraform backend

**If a azure terraform backend has already been created you can skip this step**

Terraform uses a backend to keep track of the infrastructure state. We use Azure storage to run the backend so that everyone has a synced version of the state.

To set up the terraform backend navigate to `/infrastructure/terraform_backend/` and run:

```
terraform init
```

Open the `variables.tf` file and check the subscription_id field is set to your subscription.

Then run:
```
terraform plan
```
which creates an execution plan. Check this matches your expectations. If you are happy then run:

```
terraform apply
```

to set up the azure terraform backend infrastructure. You should now be able to see this on the azure portal.


## Creating infrastructure

### LAQN VM


1. Navigate to the infrastructure directory and create a new file called `backend.tf`
    - **Ensure this file is in `.gitignore` . Do not push this file to the remote repository**

2. Copy the following into the file:

```
terraform {
  backend "azurerm" {

    storage_account_name = "cleanairterraformbackend"
    container_name       = "cleanairbackend"
    key = "cleanairkey"
    access_key           = ""
  }
}
```

3. On the azure portal in the `RG_CLEANAIR_INFRASTRUCTURE` resource group, navigate to the `cleanairterraformbackend` storage account, go to `access keys` and copy key1 into the access key field in the `backend.tf` file we just created.

4. Run the following to configure the backend:

```
terraform init
```
You should see a message saying *'Successfully configured the backend "azurerm"!'*

### Create the LAQN VM

1. Open the `variables.tf` file, and ensure the `subscription_id` and `resource_group` variables are correct.

2. Run ```terraform plan``` to check the execution plan. When you are happy run ```terraform apply``` to create the VM infrastructure.


3. Your VM should spin up and will be viewable on the portal. To connect to it you need to retrieve the VM ip addres and password (stored in a keyvault). You can retrieve them with:

```
az vm show --resource-group myResourceGroup --name myVM -d --query [publicIps] --o tsv
```

```
az keyvault secret show --name "laqn-admin-password" --vault-name "kvpasswords" --output table
```

4. Test your vm by ssh:

```
ssh atiadmin@{vm_public_ip}
```

replacing {vm_public_ip} with the vm's public ip.

### Destroy the VM and all resources

To destroy all the resources created in the previous step run:

```
terraform destroy
```

You can check everything was removed on the azure portal.