# Setting up a local kubernetes cluster with minikube

### Consider using Lens

[Lens](https://k8slens.dev/) is recommended as a kubernetes IDE to view the cluster

## Setup

1. Download [minikube with ingress control enabled](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/) (see `Create a Minikube cluster` and `Enable the Ingress controller`)

    - Make sure you start the cluster with at least 3 cpus and use 
```bash
minikube start --cpus 3 --vm=true
```
Enable ingress

```bash
minikube addons enable ingress
```

2. Make sure helm points to your local cluster (**not production if you have access to it**).
```bash
kubectl config view
```
The current context should be minikube

3. Add a secrets file to the cluster

    - Authenticate with azure and generate a token 
    - create a secret file
```bash
echo '{
    "username": "<turing-credentials>@cleanair-inputs-server",
    "host": "cleanair-inputs-server.postgres.database.azure.com",
    "port": 5432,
    "db_name": "cleanair_inputs_db",
    "ssl_mode": "require",
    "password": "<get-a-token-and-place-here"
}' > db_secrets.json
```

Add to cluster
```bash
kubectl create secret generic secrets --from-file=db_secrets.json
```


3. Use minikubes docker daemon

```bash
eval $(minikube docker-env)
```

4. Build a local docker image:
```bash 
docker build -t urbanairapi:local -f containers/dockerfiles/urbanairapi.Dockerfile 'containers'
```
5. Update helm dependencies:
```bash
helm dependency update kubernetes/cleanair
```

6. Install local version of chart:

```bash
helm install cleanairlocal kubernetes/cleanair -f kubernetes/cleanair/values_dev.yaml
```

7. Find out your IP:

```bash
minikube ip
```

8. In a browser enter the IP and test out:

```
/
/welcome/
```
Try the hyperlinks to the docs pages

`/dev/packages/cleanair`
