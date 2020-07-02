# UrbanAir API

The UrbanAir RESTFUL API is a [Fast API](https://fastapi.tiangolo.com/) application. To run it in locally you must configure the following steps:

### Configure CleanAir database secrets
Ensure you have configured a secrets file for the CleanAir database 

```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

### Run the application

### On development server
```bash 
DB_SECRET_FILE=$(pwd)/.secrets/.db_secrets_ad.json uvicorn urbanair.main:app --reload
```

### In a docker image

To build the API docker image
```bash
docker build -t fastapi:test -f containers/dockerfiles/urbanairapi.Dockerfile 'containers'
```

The run the docker image:

```bash
DB_SECRET_FILE='.db_secrets_ad.json'
SECRET_DIR=$(pwd)/.secrets  
docker run -i -p 80:80 -e DB_SECRET_FILE -e PGPASSWORD -e APP_MODULE="urbanair.main:app" -e IS_DOCKER=true -v $SECRET_DIR:/secrets fastapi:test
```