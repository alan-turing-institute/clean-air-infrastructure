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
pip install -r requirements.txt
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
`Terraform` uses a backend to keep track of the infrastructure state.
We keep the backend in `Azure` storage so that everyone has a synchronised version of the state.

To enable this, we have to create an initial `Terraform` configuration by running:

```
python initialise_terraform.py
```

This will only need to be run once (by anyone), but it's not a problem if you run it multiple times.


## Building the Clean Air infrastructure with Terraform
To build the `Terraform` infrastructure go to the `terraform` directory and run:

```
terraform init
```

If you want to, you can look at the `config.tf` file, which should contain various details of your `Azure` subscription. **NB. It is important that this file is in `.gitignore` . Do not push this file to the remote repository**

Then run:

```
terraform plan
```

which creates an execution plan. Check this matches your expectations. If you are happy then run:

```
terraform apply
```

to set up the Clean Air infrastructure on `Azure` using `Terraform`. You should be able to see this on the `Azure` portal.


## Accessing the Clean Air infrastructure
At this point, the LAQN virtual machine should be spun up and be viewable on the portal.
To connect to it you need to retrieve its IP address and password (stored in a keyvault). You can retrieve them with:

```
az vm list-ip-addresses --resource-group RG_CLEANAIR_DATASOURCES --name LAQN-VM --query "[].virtualMachine.network.publicIpAddresses[].ipAddress" --output tsv
```

```
az keyvault secret show --vault-name "$(az keyvault list --resource-group='RG_CLEANAIR_INFRASTRUCTURE' --query '[0].name' --output tsv)" --name "laqn-vm-admin-password" --query "value" --output tsv
```


You can now log in to your virtual machine using `ssh`:

```
ssh atiadmin@{vm_public_ip}
```

replacing {vm_public_ip} with the public IP address that you previously obtained.

### Destroy the VM and all resources

To destroy all the resources created in the previous step run:

```
terraform destroy
```

You can check everything was removed on the azure portal.