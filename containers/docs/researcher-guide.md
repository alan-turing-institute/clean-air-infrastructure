# Researcher guide

*The following steps provide useful tools for researchers to use, for example jupyter notebooks.*

## Setup notebook

First install jupyter with conda (you can also use pip).

```bash
pip install jupyter
```

You can start the notebook:

```bash
jupyter notebook
```

### Environment variables

To access the database, the notebooks need access to the `PGPASSWORD` environment variable.
It is also recommended to set the `SECRETS` variable.
We will create a `.env` file within you notebook directory `path/to/notebook` where you will be storing environment variables.

> **Note**: if you are using a shared system or scientific cluster, **do not follow these steps and do not store your password in a file**.

Run the below command to create a `.env` file, replacing `path/to/secretfile` with the path to your `db_secrets`.

```bash
echo '
SECRETS="path/to/secretfile"
PGPASSWORD=
' > path/to/notebook/.env
```

To set the `PGPASSWORD`, run the following command.
This will create a new password using the azure cli and replace the line in `.env` that contains `PGPASSWORD` with the new password.
Remember to replace `path/to/notebook` with the path to your notebook directory.

```bash
sed -i '' "s/.*PGPASSWORD.*/PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)/g" path/to/notebook/.env
```

If you need to store other environment variables and access them in your notebook, simply add them to the `.env` file.

To access the environment variables, include the following lines at the top of your jupyter notebook:

```python
%load_ext dotenv
%dotenv
```

You can now access the value of these variables as follows:

```python
secretfile = os.getenv("SECRETS", None)
```

Remember that the `PGPASSWORD` token will only be valid for ~1h.
