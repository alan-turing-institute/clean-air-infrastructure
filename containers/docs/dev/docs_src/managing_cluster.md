Login to azure (see main README)

```bash
az login
```

Set the correct subscription:

```bash
az account set --subscription "UrbanAir" 
```

Get the cluster credentials:

```bash
az aks get-credentials --resource-group RG_CLEANAIR_KUBERNETES_CLUSTER --name cleanair-kubernetes
```

Optionally install [Lens](https://k8slens.dev/).

