data "helm_repository" "datasources" {
    name = "helm_datasources"
    url  = "https://kubernetes-charts-incubator.storage.googleapis.com"
}

resource "helm_release" "my_cache" {
    name       = "my-cache"
    repository = "${data.helm_repository.incubator.metadata.0.name}"
    chart      = "redis-cache"
}


