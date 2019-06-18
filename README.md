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

### Travis CI CLI
 Ensure you have Ruby installed:
```
ruby -v
```

Then install the Travis CI CLI with:

```
gem install --user-install travis -v 1.8.10 --no-rdoc --no-ri
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

Login to travis with your github credentials, making sure you are in the clean air repository (travis automatically detects your repository):

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


<!-- ### Setting up webhooks in the GitHub repository
NB. This only needs to be done once but is documented here for better reproducibility in future.
- Run `python get_github_keys.py` to get the SSH keys and webhook settings for each of the relevant servers

#### Add deployment keys to GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Deploy keys` and click on `Add deploy key`
- Paste the key into `Key` and give it a memorable title (like `laqn-cleanair`)

#### Enable webhooks in GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Webhooks` and click on `Add webhook`
- Set the `Payload URL` to the value given by `get_github_keys.py`
- Set the `Content type` to `application/json` (not required but preferred)
- Select `Let me select individual events` and tick `Pull requests` only -->


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

## Add static resources

Terraform will now have created a number of databases. In addition, it creates a hidden folder called `.secrets` in the terraform directory which contains login information for the databases (these are also stored in the cleanair KeyVault). 

NB: To run the next step ensure Travis runs a build (this will place the docker files in the azure container registry that was provisioned by terraform. 

The following static datasets need to be manually inserted into the corresponding databases:

1. Login to the container registry:

```
docker login <AzureContainerReg>
```

2. Ensure PostGIS extention is installed in database. Execute the following SQL code in the database:
```
CREATE EXTENSION IF NOT EXISTS postgis;
```

3. Run the docker image with the database secret and datafile mounted:
```
docker run -it -v <absolutepathtosecrets>/.ukmap_secret.json:/.secrets/.secret.json -v /<AbsolutePathToUKMapGDBFolder>/UKMap.gdb:/data/static_data.gdb <AzureContainerReg>/insert_static_datasource:latest
```

### Destroy all resources

To destroy all the resources created in the previous step run:

```
terraform destroy
```

You can check everything was removed on the Azure portal.

Then login to TravisCI and delete the Azure Container repo environment variables. 


<!-- ## Configuring CI pipeline
To add the Azure container registry (ACR) login details to Travis, navigate to the Azure portal and find the ACR username and password. Navigate to Travis repository -> settings and add these as environment variables: ACR_USERNAME ACR_PASSWORD  -->

## Configure local Kubernetes Cluster:

Install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/) on your machine 


To start the cluster run: 
```
minikube start
```

Start the cluster dashboard with:

```
minikube dashboard
```

Next install [helm](https://helm.sh/docs/using_helm/). 

### Adding secrets

The cluster requires secrets in order to pull images from the azure container repository and to connect to databases. When terraform provisioned the azure infrastructure it creates a folder called `.secrets/` which contains a number of files. We need to add these to the kubernetes cluster. 

```
kubectl create secret docker-registry regcred --docker-server=<servername> --docker-username=<username>--docker-password=<password> --docker-email=<your-email>
```

Next create a secret for each database secret file:

```
kubectl create secret generic <datasource>cred --from-file=<file>
```


### Helm Cheatsheet

To see the rendered manifest file:
```
helm install cleanair --dry-run --debug
```

To install run:

```
helm install cleanair
```

## Data Source docker files

Datasources consist of a docker image which collect data from an API and store them in a database. These images are stored in an Azure Container Registry and are pulled by the Kubernetes cluster. However, it may be useful to run these locally on occasion:

The following command runs the laqn docker image and mounts the secrets file to the correct location in the container. 

```
docker run -v <localdirectorycontaininglaqnsecretfile>:/secrets/laqncred/ <laqnimage>
```