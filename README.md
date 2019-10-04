# clean-air-infrastructure
Azure Infrastructure for the Clean Air project

# Prerequisites
To run this project you will need:

- an `Azure account` (the cloud-computing platform where the infrastructure is deployed)
- the `Azure command line interface (CLI)` (for managing your Azure subscriptions)
- the `Azure Python SDK` (for managing the initial setup)
- `Terraform` (for configuring the Azure infrastructure)
- the `Travis Continuous Integration (CI) CLI` (for setting up automatic deployments)
- `Docker` (For building and testing images locally)


## Azure Account
If you do not have an `Azure` account already, please [`follow the procedure here`](https://azure.microsoft.com/en-us/) to get started with an `Azure` subscription.


## Azure CLI
If you have not already installed the command line interface for `Azure`, please [`follow the procedure here`](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) to get started.


## Azure Python SDK
You can install the `Azure` Python SDK with `pip` using:

```
pip install -r containers/requirements.txt
```


## Terraform
The Azure infrastructure is managed with `Terraform`. To get started [download `Terraform` from here](https://www.terraform.io). If using Mac OS, you can instead use `homebrew`:

```
brew install terraform
```


## Travis CI CLI
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



# Setting up the Clean Air infrastructure
The following steps are needed to setup the Clean Air cloud infrastructure.


## Setup Azure
To start working with `Azure`, you must first login to your account from the terminal:

```
az login
```

Check which `Azure` subscriptions you have access to by running

```
az account list --output table --refresh
```

Then set your default subscription to the Clean Air project (if you cannot see it in the output generated from the last line you do not have access):


```
az account set --subscription "CleanAir"
```


## Login to Travis CLI

Login to travis with your github credentials, making sure you are in the Clean Air repository (travis automatically detects your repository):

```
travis login --pro
```


## Setup Terraform with Python
`Terraform` uses a backend to keep track of the infrastructure state.
We keep the backend in `Azure` storage so that everyone has a synchronised version of the state.

To enable this, we have to create an initial `Terraform` configuration by running (from the root directory):

```
python setup/initialise_terraform.py -i <AWS_KEY_ID> -k <AWS_KEY>
```

Where `AWS_KEY_ID` and `AWS_KEY` are the secure key information needed to access TfL's SCOOT data on Amazon Web Services.
This will only need to be run once (by anyone), but it's not a problem if you run it multiple times.


## Building the Clean Air infrastructure with Terraform
To build the `Terraform` infrastructure go to the `terraform` directory and run:

```
terraform init
```

If you want to, you can look at the `backend_config.tf` file, which should contain various details of your `Azure` subscription.
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



# Initialising the input databases
Terraform will now have created a number of databases. We need to add the datasets to the database.

This is done using Docker images from the Azure container registry.
These Docker images are built by Travis whenever commits are made to the GitHub repository.

To run the next steps we need to ensure that Travis runs a build in order to add the Docker images to the Azure container registry created by Terraform.
Either push to the GitHub repository, or rerun the last build by going to https://travis-ci.com/alan-turing-institute/clean-air-infrastructure/ and clicking on the `Restart build` button.
This will build all of the Docker images and add them to the registry.


## Add static datasets
Static datasets (like StreetCanyons or UKMap) only need to be added to the database once - after setting up the infrastructure.
We will do this manually, using a Docker image from the Azure container registry.
Please note that you may need to increase the available memory under `Docker > Preferences... > Advanced` (the following instructions were tested using 8 GB).

**NB. If running on OS X, ensure that you have added `/var/folders` as a shareable directory in `Docker > Preferences... > File Sharing`. Ensure you have pushed your latest commit to github if working on a branch**

From the root directory, running the command

```
python setup/insert_static_datasets.py
```

will download the static datasets to temporary local storage and then upload them to the database.
The process takes approximately 1hr (most of this is for the UKMap data) and you must have internet connectivity throughout.

## Adding live datasets
The live datasets (like LAQN or AQE) are populated using daily jobs that create an Azure container instance and add the most recent data to the database.
We tell this job which version of the container to run by using GitHub webhooks which keep track of changes to the master branch.

### Setting up webhooks in the GitHub repository
- Run `python setup/get_github_keys.py` to get the SSH keys and webhook settings for each of the relevant servers
- In GitHub go to `clean-air-infrastructure > Settings > Deploy keys` and click on `Add deploy key`
- Paste the key into `Key` and give it a memorable title (like `laqn-cleanair`)

### Enable webhooks in GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Webhooks` and click on `Add webhook`
- Set the `Payload URL` to the value given by `get_github_keys.py`
- Set the `Content type` to `application/json` (not required but preferred)
- Select `Let me select individual events` and tick `Pull requests` only



# Miscellaneous

## Running without Azure
It is possible to test code without the Azure infrastructure. This can be achieved by creating databases on your local machine. Ensure you install the following:

```bash
brew install postgresql postgis
```

Create a database called `cleanair_db` and add the following login details (make sure they match the database credentials) to `/terraform/.secrets/.db_input_secret.json`:

```json
{
    "username": "<username>",
    "password": "<password>",
    "host": "host.docker.internal",
    "port": 5432,
    "db_name": "cleanair_db",
    "ssl_mode": "prefer"
}
```

To upload static data to the local database run:

```
python setup/insert_static_datasets.py -l <full-path-to-secret-file>
```

where the secret file is a JSON file of the form detailed above.


## Removing Terraform infrastructure
To destroy all the resources created by `Terraform` run:

```
terraform destroy
```

You can check everything was removed on the Azure portal.
Then login to TravisCI and delete the Azure Container repo environment variables.
















<!-- ## Configure Kubernetes Cluster:

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

-->