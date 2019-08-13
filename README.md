# clean-air-infrastructure
Azure Infrastructure for the Clean Air project



## Prerequisites
To run this project you will need:

- an `Azure account` (the cloud-computing platform where the infrastructure is deployed)
- the `Azure command line interface (CLI)` (for managing your Azure subscriptions)
- the `Azure Python SDK` (for managing the initial setup)
- `Terraform` (for configuring the Azure infrastructure)
- the `Travis Continuous Integration (CI) CLI` (for setting up automatic deployments)


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

### Travis CI CLI
 Ensure you have Ruby 1.9.3 or above installed:
```
ruby -v
```

Then install the Travis CI CLI with:

```
gem install --user-install travis -v 1.8.10 --no-rdoc --no-ri
```

On some versions of OSX, this fails, so you may need the following alternative:
```
ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future gem install --user-install travis -v 1.8.10 --no-rdoc --no-ri
```

Verify with
```
travis version
```

If this fails ensure Gems user_dir is on the path:

```
cat << EOF >> ~/.bash_profile
export PATH="\$PATH:$(ruby -e 'puts Gem.user_dir')/bin"
EOF
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


### Login to Travis CLI

Login to travis with your github credentials, making sure you are in the Clean Air repository (travis automatically detects your repository):

```
travis login --pro
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

If you want to, you can look at the `config.tf` file, which should contain various details of your `Azure` subscription.
**NB. It is important that this file is in `.gitignore` . Do not push this file to the remote repository**

Then run:

```
terraform plan
```

which creates an execution plan. Check this matches your expectations. If you are happy then run:

```
terraform apply
```

to set up the Clean Air infrastructure on `Azure` using `Terraform`. You should be able to see this on the `Azure` portal.


### Add static resources (Only run if you are setting up the infrastructure - not required if already exists)
Terraform will now have created a number of databases. We need to add the datasets to the database.


NB: To run the next step ensure Travis runs a build (this will place the docker files in the azure container registry that was provisioned by terraform).
Either push the the repo, or go to travis and rerun the last build.

1. Run `download_static_datasets.py` to download the static datasets from Azure blob storage.

2. When terraform created the Azure Container registry it created a local (gitignored) file: `/terraform/.secrets/static_data_docker_insert.sh`. From the root of the repository run the following to insert the datasets:

```
bash static_data_local/insert_static_data.sh
```


## Setting up webhooks in the GitHub repository
NB. This only needs to be done once but is documented here for better reproducibility in future.
- Run `python get_github_keys.py` to get the SSH keys and webhook settings for each of the relevant servers


### Add deployment keys to GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Deploy keys` and click on `Add deploy key`
- Paste the key into `Key` and give it a memorable title (like `laqn-cleanair`)


### Enable webhooks in GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Webhooks` and click on `Add webhook`
- Set the `Payload URL` to the value given by `get_github_keys.py`
- Set the `Content type` to `application/json` (not required but preferred)
- Select `Let me select individual events` and tick `Pull requests` only -->



## Configure Kubernetes Cluster:

### Local cluster
You can set up a local cluster on your machine. To do this install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)


To start the cluster run:
```
minikube start
```

Start the cluster dashboard with:

```
minikube dashboard
```

Next follow these instruction to [install helm](https://helm.sh/docs/using_helm/).

### Adding secrets

The cluster requires secrets in order to pull images from the azure container repository and to connect to databases. When terraform provisioned the azure infrastructure it creates a folder called `.secrets/` which contains a number of files. We need to add these to the Kubernetes cluster.

The ACR login details are in a file called .regcred_secret.json
```
kubectl create secret docker-registry regcred --docker-server=<servername> --docker-username=<username>--docker-password=<password> --docker-email=<your-email>
```

Next create a secret for each database secret file:
```
kubectl create secret generic <datasource>cred --from-file=<file>
```


### Configure the cluster with Helm

Go to the `/kubernetes` directory and run:

```
helm package cleanair
```


To see the rendered manifest file which will be installed on the kuberenets cluster run:
```
helm install cleanair --dry-run --debug
```

To install run:

```
helm install cleanair
```

Now you to the minikube dashboard and you can see everything that was installed.

## Data Source docker files

Datasources consist of a docker image which collect data from an API and store them in a database. These images are stored in an Azure Container Registry and are pulled by the Kubernetes cluster. However, it may be useful to run these locally on occasion:

The following command runs the laqn docker image and mounts the secrets file to the correct location in the container.

```
docker run -v <localdirectorycontaininglaqnsecretfile>:/secrets/ <laqnimage>
```



## Removing Terraform infrastructure
To destroy all the resources created by `Terraform` run:

```
terraform destroy
```

You can check everything was removed on the Azure portal.
Then login to TravisCI and delete the Azure Container repo environment variables.