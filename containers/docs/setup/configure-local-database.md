# Configure a local database
In production we use a managed [PostgreSQL database](https://docs.microsoft.com/en-us/azure/postgresql/). However, it is useful to have a local copy to run tests and for development. To set up a local version start a local postgres server:

```bash 
brew services start postgresql   
```

<details>
<summary> If you installed the database using conda </summary>

Set it up the server and users first with:

```bash
initdb -D mylocal_db
pg_ctl -D mylocal_db -l logfile start
createdb --owner=${USER} myinner_db
```

When you want to work in this environment again you'll need to run:
```bash
pg_ctl -D mylocal_db -l logfile start
```

You can stop it with:
```bash
pg_ctl -D mylocal_db stop
```
</details>

### Create a local secrets file
We store database credentials in json files. **For production databases you should never store database passwords in these files - for more information see the production database section**. 

```bash
mkdir -p .secrets
echo '{
    "username": "postgres",
    "password": "''",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}' >> .secrets/.db_secrets_offline.json
```

N.B In some cases your default username may be your OS user. Change the username in the file above if this is the case.

```bash
createdb cleanair_test_db
```

### Create Schema and roles

We must now setup the database schema. This also creates a number of roles on the database.

Create a variable with the location of your secrets file

```bash
SECRETS=$(pwd)/.secrets/.db_secrets_offline.json
```

```bash
python containers/entrypoints/setup/configure_db_roles.py -s $SECRETS -c configuration/database_role_config/local_database_config.yaml   
```

### Static data insert

The database requires a number of static datasets. We can now insert `static data` into our local database. You will need a [SAS token](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview) to access static data files stored on Azure. 

If you have access Azure you can log in to Azure from the [command line](#login-to-Azure) and run the following to obtain a SAS token:

```bash
SAS_TOKEN=$(python containers/entrypoints/setup/insert_static_datasets.py generate)
```

By default the SAS token will last for 1 hour. If you need a longer expiry time pass `--days` and `--hours` arguments to the program above. N.B. It's better to use short expiry dates where possible. 

Otherwise you must request a SAS token from an [infrastructure developer](#contributors-:dancers:) and set it as a variable:

```bash
SAS_TOKEN=<SAS_TOKEN>
```

You can then download and insert all static data into the database by running the following:

```bash
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $SECRETS -d rectgrid_100 street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector urban_village
```

If you would also like to add `UKMAP` to the database run:

```bash
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $SECRETS -d ukmap
```

`UKMAP` is extremly large and will take ~1h to download and insert. We therefore do not run tests against `UKMAP` at the moment. 

N.B SAS tokens will expire after a short length of time, after which you will need to request a new one. 



### Check the database configuration

You can check everything configured correctly by running:

```bash
pytest containers/tests/test_database_init --secretfile $SECRETS
```

