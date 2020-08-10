# Azure account

To contribute to the Turing deployment of this project you will need to be on the Turing Institute's Azure active directory. In other words you will need a turing email address `<someone>@turing.ac.uk`. If you do not have one already contact an infrastructure administrator.

If you are deploying the CleanAir infrastructure elsewhere you should have access to an Azure account (the cloud-computing platform where the infrastructure is deployed).

## Login to Azure

To start working with `Azure`, you must first login to your account from the terminal:
```bash
az login
```

### Infrastructure developers:

Infrastructure developers should additionally check which `Azure` subscriptions you have access to by running
```bash
az account list --output table --refresh
```

Then set your default subscription to the Clean Air project (if you cannot see it in the output generated from the last line you do not have access):
```bash
az account set --subscription "CleanAir"
```

If you don't have access this is ok. You only need it to deploy and manage infrastructure. 