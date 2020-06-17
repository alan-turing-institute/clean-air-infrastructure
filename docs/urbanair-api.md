# UrbanAir API

The UrbanAir RESTFUL API is a [Flask](https://flask.palletsprojects.com/en/1.1.x/quickstart/) application. To run it in locally you must configure the following steps:

### Configure CleanAir database secrets
Ensure you have configured a secrets file for the CleanAir database as documented [above](#create-secret-file-to-connect-using-CleanAir-package). You will also need to set the [`PGPASSWORD` environment variable](#entry-point-with-production-database)

```bash
export DATABASE_SECRETFILE=$(pwd)/.secrets/.db_secrets_ad.json
```

### Enable Flask development server

```bash
export FLASK_ENV=development 
```

You can now run the API

```bash
python containers/urbanair/wsgi.py
```
