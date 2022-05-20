# Cheat sheet

Useful commands that you will use regularly when developing code.
We assume you have [installed cleanair](installation.md) and [logged into Azure CLI](azure.md#sign-into-the-azure-cli).

## Database connections

```bash
# connect to the production database
urbanair init production

# print your Azure database username & access token
urbanair echo dbuser
urbanair echo dbtoken

# get the path to the urbanair CLI secrets file
export DB_SECRET_FILE="$(urbanair config path)/.db_secrets.json"
```
