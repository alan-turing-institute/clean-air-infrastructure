# Infrastructure Deployment

**The following steps are needed to setup the Clean Air cloud infrastructure. Only infrastrucure administrator should deploy**

## Login to Travis CLI
Login to Travis with your github credentials, making sure you are in the Clean Air repository (Travis automatically detects your repository):

```bash
travis login --pro
```

Create an Azure service principal using the documentation for the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli) or with [Powershell](https://docs.microsoft.com/en-us/powershell/azure/create-azure-service-principal-azureps), ensuring that you keep track of the `NAME`, `ID` and `PASSWORD/SECRET` for the service principal, as these will be needed later.


## Setup Terraform with Python  
`Terraform` uses a backend to keep track of the infrastructure state.
We keep the backend in `Azure` storage so that everyone has a synchronised version of the state.

<details>
<summary> You can download the `tfstate` file with `az` though you won't need it.</summary>

```bash
cd terraform
az storage blob download -c terraformbackend -f terraform.tfstate -n terraform.tfstate --account-name terraformstorage924roouq --auth-mode key
```

</details>


To enable this, we have to create an initial `Terraform` configuration by running (from the root directory):

```bash
python cleanair_setup/initialise_terraform.py -i $AWS_KEY_ID -k $AWS_KEY -n $SERVICE_PRINCIPAL_NAME -s $SERVICE_PRINCIPAL_ID -p $SERVICE_PRINCIPAL_PASSWORD
```

Where `AWS_KEY_ID` and `AWS_KEY` are the secure key information needed to access TfL's SCOOT data on Amazon Web Services.

```bash
AWS_KEY=$(az keyvault secret show --vault-name terraform-configuration --name scoot-aws-key -o tsv --query value)
AWS_KEY_ID=$(az keyvault secret show --vault-name terraform-configuration --name scoot-aws-key-id -o tsv --query value)
```

And `SERVICE_PRINCIPAL`'s  `NAME`, `ID` and `PASSWORD` are also available in the `terraform-configuration` keyvault.

```bash
SERVICE_PRINCIPAL_NAME=$(az keyvault secret show --vault-name terraform-configuration --name azure-service-principal-name -o tsv --query value)
SERVICE_PRINCIPAL_ID=$(az keyvault secret show --vault-name terraform-configuration --name azure-service-principal-id -o tsv --query value)
SERVICE_PRINCIPAL_PASSWORD=$(az keyvault secret show --vault-name terraform-configuration --name azure-service-principal-password -o tsv --query value)
```

This will only need to be run once (by anyone), but it's not a problem if you run it multiple times.


## Building the Clean Air infrastructure with Terraform
To build the `Terraform` infrastructure go to the `terraform` directory

```bash
cd terraform
```

and run:

```bash
terraform init
```

If you want to, you can look at the `backend_config.tf` file, which should contain various details of your `Azure` subscription.
**NB. It is important that this file is in `.gitignore` . Do not push this file to the remote repository**

Then run:
```bash
terraform plan
```

which creates an execution plan. Check this matches your expectations. If you are happy then run:
```bash
terraform apply
```

to set up the Clean Air infrastructure on `Azure` using `Terraform`. You should be able to see this on the `Azure` portal.



## Creating A Record for cleanair API (DO THIS BEFORE RUNNING AZURE PIPELINES)
Terraform created a DNS Zone in the kubernetes cluster resource group (`RG_CLEANAIR_KUBERNETES_CLUSTER`). Navigate to the DNS Zone on the Azure portal and copy the four nameservers in the “NS” record. Send the nameserver to Turing IT Services. Ask them to add the subdomain’s DNS record as an NS record for `urbanair` in the `turing.ac.uk` DNS zone record.

1. When viewing the DNS zone on the Azure Portal, click `+ Record set`
2. In the Name field, enter `urbanair`.
3. Set Alias record set to “Yes” and this will bring up some new options.
4. We can now set up Azure pipelines. Once the cleanair api has been deployed on kubernetes you can update the alias record to point to the ip address of the cleanair-api on the cluster.


## Initialising the input databases
Terraform will now have created a number of databases. We need to add the datasets to the database.
This is done using Docker images from the Azure container registry.
You will need the username, password and server name for the Azure container registry.
All of these will be stored as secrets in the `RG_CLEANAIR_INFRASTRUCTURE > cleanair-secrets` Azure KeyVault.

<!-- ## Using Travis (old)
These Docker images are built by Travis whenever commits are made to the GitHub repository.
Add `ACR_PASSWORD`, `ACR_SERVER` and `ACR_USERNAME` as Travis secrets.

To run the next steps we need to ensure that Travis runs a build in order to add the Docker images to the Azure container registry created by Terraform.
Either push to the GitHub repository, or rerun the last build by going to https://travis-ci.com/alan-turing-institute/clean-air-infrastructure/ and clicking on the `Restart build` button.
This will build all of the Docker images and add them to the registry. -->

## Setting up Azure pipelines
These Docker images are built by an Azure pipeline whenever commits are made to the master branch of the GitHub repository.
Ensure that you have configured Azure pipelines to [use this GitHub repository](https://docs.microsoft.com/en-us/azure/devops/pipelines/get-started/pipelines-get-started).
You will need to add Service Connections to GitHub and to Azure (the Azure one should be called `cleanair-scn`).
Currently a pipeline is set up [here](https://dev.azure.com/alan-turing-institute/clean-air-infrastructure/_build).

To run the next steps we need to ensure that this pipeline runs a build in order to add the Docker images to the Azure container registry created by Terraform.
Either push to the GitHub repository, or rerun the last build by going to [the Azure pipeline page](https://dev.azure.com/alan-turing-institute/clean-air-infrastructure/_build) and clicking `Run pipeline` on the right-hand context menu.
This will build all of the Docker images and add them to the registry.

Now go to Azure and update the A-record to point to the ip address of the cleanair-api on the cluster.

## Add static datasets
To add static datasets follow the [Static data insert](#static-data-insert) instructions but use the production database credentials

## Adding live datasets
The live datasets (like LAQN or AQE) are populated using regular jobs that create an Azure container instance and add the most recent data to the database.
These are run automatically through Kubernetes and the Azure pipeline above is used to keep track of which version of the code to use.

## Kubernetes deployment with GPU support

The [azure pipeline](#setting-up-azure-pipelines) will deploy the cleanair helm chart to the azure kubernetes cluster we deployed with terraform. If you deployed GPU enabled machines on Azure (current default in the terraform script) then you need to install the nvidia device plugin daemonset. The manifest for this is [adapted from the Azure docs](https://docs.microsoft.com/en-us/azure/aks/gpu-cluster). However, as our GPU machines have [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/#:~:text=Taints%20are%20the%20opposite%20%E2%80%93%20they,not%20scheduled%20onto%20inappropriate%20nodes.) applied we have to add tolerations to the manifest, otherwise the nodes will block the daemonset. To install the custom manifest run,


```bash
kubectl apply -f kubernetes/gpu_resources/nvidia-device-plugin-ds.yaml
```

<!-- 
## Configure certificates

https://cert-manager.io/docs/tutorials/acme/ingress/

## Uninstalling a failed helm install (warning - this will uninstall everything from the cleanair namespace on the cluster)

If the first helm install fails you may need to manually remove certmanager resources from the cluster with


```bash
helm uninstall cleanair --namespace cleanair
```

```bash
kubectl get -n cleanair crd
kubectl delete -n cert-manager crd --all
kubectl delete namespaces cleanair
```

Cluster roles may not be removed. Remove them with:
```bash
kubectl get clusterrole  | grep 'cert-manager'|awk '{print $1}'| xargs kubectl delete clusterrole
kubectl get role --namespace kube-system  | grep 'cert-manager'|awk '{print $1}'| xargs kubectl delete role --namespace kube-system
kubectl get clusterrolebindings | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete clusterrolebindings
kubectl get mutatingwebhookconfigurations | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete mutatingwebhookconfigurations
kubectl get validatingwebhookconfigurations  | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete validatingwebhookconfigurations
kubectl get rolebindings --namespace kube-system | grep 'cert-manager'|awk '{print $1}'|xargs kubectl delete rolebindings --namespace kube-system
kubectl get clusterrole  | grep 'nginx'|awk '{print $1}'| xargs kubectl delete clusterrole
kubectl get clusterrolebindings | grep 'nginx'|awk '{print $1}'|xargs kubectl delete clusterrolebindings

```

If helm wont install the chart after this check all api services are working:

```bash
kubectl get apiservice
```

Deleteing the failed api service may resolve this issue:

```bash
kubectl delete apiservice v1beta1.metrics.k8s.io
```


Follow theses instructions https://cert-manager.io/docs/tutorials/acme/ingress/ -->

<!-- We tell this job which version of the container to run by using GitHub webhooks which keep track of changes to the master branch.

### Setting up webhooks in the GitHub repository
- Run `python cleanair_setup/get_github_keys.py` to get the SSH keys and webhook settings for each of the relevant servers
- In GitHub go to `clean-air-infrastructure > Settings > Deploy keys` and click on `Add deploy key`
- Paste the key into `Key` and give it a memorable title (like `laqn-cleanair`)

### Enable webhooks in GitHub
- In GitHub go to `clean-air-infrastructure > Settings > Webhooks` and click on `Add webhook`
- Set the `Payload URL` to the value given by `get_github_keys.py`
- Set the `Content type` to `application/json` (not required but preferred)
- Select `Let me select individual events` and tick `Pull requests` only -->

## Removing Terraform infrastructure
To destroy all the resources created by `Terraform` run:
```
terraform destroy
```

You can check everything was removed on the Azure portal.
Then login to TravisCI and delete the Azure Container repo environment variables.


