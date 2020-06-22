# Non-infrastructure dependencies 

To contribute as a non-infrastructure developer you will need the following:

- `Azure command line interface (CLI)` (for managing your Azure subscriptions)
- `Docker` (For building and testing images locally)
- `postgreSQL` (command-line tool for interacting with db)
- `CleanAir python packages` (install python packages)
- `GDAL` (For inserting static datasets)

The instructions below are to install the dependencies system-wide, however you can
follow the [instructions at the end if you wish to use an anaconda environment](#with-a-Conda-environment)
if you want to keep it all separated from your system.

Windows is not supported. However, you may use [Windows Subsystem for Linux 2](https://docs.microsoft.com/en-us/windows/wsl/install-win10) and then install dependencies with [conda](#with-a-conda-environment).

### Azure CLI
If you have not already installed the command line interface for `Azure`, please [`follow the procedure here`](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) to get started

<details>
<summary>Or follow a simpler option</summary>
Install it using on your own preferred environment with `pip install azure-cli`
</details>

### Docker
Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

### PostgreSQL

[PostgreSQL](https://www.postgresql.org/download) and [PostGIS](https://postgis.net/install).

```bash
brew install postgresql postgis
```

### GDAL

[GDAl](https://gdal.org/) can be installed using `brew` on a mac
```bash
brew install gdal
```

or any of the [binaries](https://gdal.org/download.html#binaries) provided for different platforms.


### Development tools
The following are optional as we can run everything on docker images. However, they are recommended for development/testing and required for setting up a local copy of the database. 

```bash
pip install -r containers/requirements.txt
```

### CleanAir Python packages
To run the CleanAir functionality locally (without a docker image) you can install the package with `pip`. 

For a basic install which will allow you to set up a local database run:

```bash
pip install -e 'containers/cleanair[<optional-dependencies>]'
```

Certain functionality requires optional dependencies. These can be installed by adding the following:

| Option keyword   | Functionality               |
| ------------------ | --------------------------- |
| models             | CleanAir GPFlow models      |
| traffic            | FBProphet Trafic Models     |
| dashboards         | Model fitting Dashboards    |

For getting started we recommend:

```bash
pip install -e 'containers/cleanair[models, traffic, dashboard]'
```

### UATraffic (London Busyness only)
All additional  functionality related to the London Busyness project requires:
```bash
pip install -e 'containers/odysseus'
```

### UrbanAir Flask API package
```bash
pip install -e 'containers/urbanair'
```