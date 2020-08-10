# Access Production Database

To access the production database you will need an Azure account and be given access by one of the [database adminstrators](#contributors-:dancers:). You should discuss what your access requirements are (e.g. do you need write access).To access the database first [login to Azure](azure-account.md) from the terminal. 

If you do not have an azure subscription you must use:

```bash
az login --allow-no-subscriptions
```

You can then request an access token. The token will be valid for between 5 minutes and 1 hour. Set the token as an environment variable:

```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
```

## Connect using psql

Once your IP has been whitelisted (ask the [database adminstrators](#contributors-:dancers:)), you will be able to
access the database using psql:

```bash
psql "host=cleanair-inputs-server.postgres.database.azure.com port=5432 dbname=cleanair_inputs_db user=<your-turing-credentials>@cleanair-inputs-server sslmode=require"
```
replacing `<your-turing-credentials>` with your turing credentials (e.g. `jblogs@turing.ac.uk`).

## Create secret file to connect using CleanAir package

To connect to the database using the CleanAir package you will need to create another secret file:

```bash
echo '{
    "username": "<your-turing-credentials>@cleanair-inputs-server",
    "host": "cleanair-inputs-server.postgres.database.azure.com",
    "port": 5432,
    "db_name": "cleanair_inputs_db",
    "ssl_mode": "require"
}' >> .secrets/db_secrets_ad.json
```

Make sure you then replace `<your-turing-credentials>` with your full Turing username (e.g.`jblogs@turing.ac.uk@cleanair-inputs-server`).
