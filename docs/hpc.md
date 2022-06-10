# High performance computing
## Aquifer login
Aquifer contains a NVIDIA Titan GPU useful for prototyping and experimenting with models.
If you need to models for many days or weeks at a time, perhaps one of Warwick's scientific clusters would be more suitable.

### How to connect

If you have a user account, simply use ssh:

```
ssh USERNAME@aquifer.dcs.warwick.ac.uk
```

- Print GPUs detail

```bash
sudo lshw -C display
```

### I need help!

Ask one of our admins:

| Name        | Email |
| ----------- | ----------- |
| Sueda Ciftci      | Sueda.Ciftci@warwick.ac.uk       |
| Patrick O'Hara   | Patrick.H.O-Hara@warwick.ac.uk      |

Problems with the GPUs? Maybe DCS team can help. Contact unixhelp@dcs.warwick.ac.uk

## Using docker on aquifer

After cloning the repository to run docker on aquifer you will need sudo access (ask the aquifer admin).
Prefix any docker commands you run with the **sudo** keyword, e.g.

```
sudo docker pull python:3.9
``` 

### Login to Azure container registry (London Air Quality Project)

If you are using Docker to run the London Air Quality Project models, you will want to use our pre-built docker images which can be downloaded from the Azure container registry.
You will need to be a member of the "urbanair" subscription on the Turing Institute's Azure subscription first.

To get the username and password for the Azure container registry, first [try this link](https://portal.azure.com/#@turing.ac.uk/resource/subscriptions/ce98e060-eddd-4b54-a33f-b7a6de2ec45c/resourceGroups/RG_CLEANAIR_INFRASTRUCTURE/providers/Microsoft.ContainerRegistry/registries/CleanAirDocker/accessKey).
If the link doesn't work, search for *CleanAirDocker* in the search bar, then navigate to *Access keys* under *Settings*.

Now use the command below on aquifer to login to the container registry using docker.
Remember to replace DOCKER_PASSWORD and LOGIN_SERVER with the relevant fields from the Azure container registry.

```
sudo docker info
```

```
echo DOCKER_PASSWORD | sudo docker login --password-stdin -u CleanAirDocker LOGIN_SERVER
```

or 

```
sudo docker login -p LOGIN_SERVER -u CleanAirDocker cleanairdocker.azurecr.io

then type the DOCKER_PASSWORD
```


You can test if the docker image is working with the GPU by running the `test_gpu.py` script in the `model_fitting_gpu` docker image as follows:

```
sudo docker pull cleanairdocker.azurecr.io/model_fitting_gpu:latest

sudo docker run -it --rm  cleanairdocker.azurecr.io/model_fitting_gpu:latest python /app/scripts/test_gpu.py
```