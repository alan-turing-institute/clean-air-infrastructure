# Entry points

### Running entry points

The directory [containers/entrypoints](containers/entrypoints) contains Python scripts which are then built into Docker images in  [containers/dockerfiles](containers/dockerfiles). You can run them locally. 


These are scripts which collect and insert data into the database. To see what arguments they take you can call any  of the files with the argument `-h`, for example:

```bash 
python containers/entrypoints/inputs/input_laqn_readings.py -h
```

### Entry point with local database

The entrypoints will need to connect to a database. To do so you can pass one or more of the following arguments:

1. `--secretfile`: Full path to one of the secret .json files you created in the `.secrets` directory.

2. `--secret-dict`: A set of parameters to override the values in `--secretfile`. For example you could alter the port and ssl parameters as `--secret-dict port=5411 ssl_mode=prefer`

### Entry point with production database

You will notice that the `db_secrets_ad.json` file we created does not contain a password. To run an entrypoint against a production database you must run:

```bash
az login
```
```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

When you run an entrypoint script the CleanAir package will read the `PGPASSWORD` environment variable. This will also take precedence over any value provided in the`--secret-dict` argument. 

### Docker entry point
To run an entry point from a docker file we first need to build a docker image. Here shown for the satellite input entry point:

```bash
docker build -t input_satellite:local -f containers/dockerfiles/input_satellite_readings.Dockerfile containers  
```

To run we need to set a few more environment variables. The first is the directory with secret files in:

```bash
SECRET_DIR=$(pwd)/.secrets
```

Now get a new token:

```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

Finally you can run the docker image, passing PGPASSWORD as an environment variable
(:warning: this writes data into the online database)

```bash
docker run -e PGPASSWORD -v $SECRET_DIR:/secrets input_satellite:local -s 'db_secrets_ad.json' -k <copernicus-key>
```

Here we also provided the copernicus api key which is stored in the `cleanair-secrets`
[Azure's keyvault](https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.KeyVault%2Fvaults).

If you want to run that example with the local database you can do so by:

```bash
COPERNICUS_KEY=$(az keyvault secret show --vault-name cleanair-secrets --name satellite-copernicus-key -o tsv --query value)
# OSX or Windows: change "localhost" to host.docker.internal on your db_secrets_offline.json
docker run -e PGPASSWORD -v $SECRET_DIR:/secrets input_satellite:local -s 'db_secrets_offline.json' -k $COPERNICUS_KEY
# Linux:
docker run --network host -e PGPASSWORD -v $SECRET_DIR:/secrets input_satellite:local -s 'db_secrets_offline.json' -k $COPERNICUS_KEY
```
