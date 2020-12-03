# Running jobs on the Kubernetes cluster

You run jobs manually on the cluster. Do do so first build a docker image and push it to the clean air container registry.

Make sure you are logged in to the container registry

```bash
az login
az acr login --name CleanAirDocker
```

## Build and push docker image
Now build and push an image. For example, to build and push the GPU cleanair image use,

```bash
CONTAINER="cleanairdocker.azurecr.io"
TAG="manual"
docker build --build-arg git_hash=$(git show -s --format=%H) -t $CONTAINER/model_fitting_gpu:$tag -f containers/dockerfiles/model_fitting_gpu.Dockerfile containers
docker push $CONTAINER/model_fitting_gpu:$tag
```

### Create a kubernetes manifest file

You need to create a kubernetes manifiest file. The following example is a good starting point.

You should make sure  `name` is unique. Make sure you set `image` to your docker image and provide any `command` and `arg` values.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
    name: cleanair-gpu-manual
    namespace: cleanair
spec:
    template:
      spec:
        containers:
        - name: cleanair-gpu-manual
          image:  cleanairdocker.azurecr.io/model_fitting_gpu:manual
          imagePullPolicy: Always
          command: ["bash", "/app/scripts/svgp.sh"]
          args: []
          volumeMounts:
          - name: secrets
            mountPath: "/secrets/"
            readOnly: true
          resources:
            limits:
                cpu: "6"
                nvidia.com/gpu: 1
            requests:
                cpu: "3"
                nvidia.com/gpu: 1
        restartPolicy: Never
        volumes:
        - name: secrets
          secret:
            secretName: secrets
        nodeSelector:
          agentpool: cleanairgpu
        tolerations:
          - key: "group"
            operator: "Equal"
            value: "cleanairgpu"
            effect: "NoSchedule"
        imagePullSecrets:
            - name: regcred
```

Save this to a file called `job_manifest.yaml` or similar.


### Run the job

To run the job you can use the following,

```bash
kubectl create -f job_manifest.yaml
```

or create the job using an IDE such as [Lens](https://k8slens.dev/).