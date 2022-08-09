# Generate a SAS token

**You will need to be [signed into the Azure CLI](azure.md#sign-into-the-azure-cli) for this guide.**

Some of our [datasets](datasets.md) are saved in [Azure's blob storage](https://azure.microsoft.com/en-gb/services/storage/blobs/).
To access these datasets, you will need a [SAS token](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview).

We provide a script called `insert_static_datasets.py` that prints a SAS token.
You must be signed into the [Azure CLI]((azure.md#sign-into-the-azure-cli)).

```bash
export SAS_TOKEN=$(python containers/entrypoints/setup/insert_static_datasets.py generate)
```

By default the SAS token will last for 1 hour. If you need a longer expiry time pass `--days` and `--hours` arguments to the program above. It's better to use short expiry dates where possible.