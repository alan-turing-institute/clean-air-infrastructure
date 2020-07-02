# Infrastructure dependencies
Cloud infrastructure developers will require the following in addition to the [non-infrastructure dependencies](#Non-infrastructure-development-:sparkles:).

### Infrastructure development
- `Access to the deployment Azure subscription`
- `Terraform` (for configuring the Azure infrastructure)
- `Travis Continuous Integration (CI) CLI` (for setting up automatic deployments)

### Azure subscription
You need to have access to the CleanAir Azure subscription to deploy infrastructure. If you need access contact an [infrastructure administrator](#contributors-:dancers:)

### Terraform 
The Azure infrastructure is managed with `Terraform`. To get started [download `Terraform` from their website](https://www.terraform.io). If using Mac OS, you can instead use `homebrew`:

```bash
brew install terraform
```

### Travis CI CLI
Ensure you have Ruby 1.9.3 or above installed:
```bash
brew install ruby
gem update --system
```

Then install the Travis CI CLI with:
```bash
gem install  travis -no-rdoc -no-ri
```

On some versions of OSX, this fails, so you may need the following alternative:
```
ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future gem install --user-install travis -v 1.8.13 --no-document
```

Verify with
```bash
travis version
```

If this fails ensure Gems user_dir is on the path:
```
cat << EOF >> ~/.bash_profile
export PATH="\$PATH:$(ruby -e 'puts Gem.user_dir')/bin"
EOF
```

### With a Conda environment

It's possible to set it up all with a conda environment, this way you can keep different
versions of software around in your machine. All the steps above can be done with:

```bash
# Non-infrastructure dependencies

conda create -n busyness python=3.7
conda activate busyness
conda install -c anaconda postgresql
conda install -c conda-forge gdal postgis uwsgi
pip install azure-cli
pip install azure-nspkg azure-mgmt-nspkg
# The following fails with: ERROR: azure-cli 2.6.0 has requirement azure-storage-blob<2.0.0,>=1.3.1, but you'll have azure-storage-blob 12.3.0 which is incompatible.
# but they install fine.
pip install -r containers/requirements.txt
pip install -e 'containers/cleanair[models, dashboard]'
pip install -e 'containers/odysseus'
pip install -e 'containers/urbanair'

## Infrastructure dependencies

# if you don't get rb-ffi and rb-json you'll need to install gcc_linux-64 and libgcc to build these in order to install travis.
conda install -c conda-forge terraform ruby rb-ffi rb-json
# At least on Linux you'll need to dissable IPV6 to make this version of gem to work.
gem install  travis -no-rdoc -no-ri
# Create a soft link of the executables installed by gem into a place seen within the conda env.
conda_env=$(conda info --json | grep -w "active_prefix" | awk '{print $2}'| sed -e 's/,//' -e 's/"//g')
ln -s $(find $conda_env -iname 'travis' | grep bin) $conda_env/bin/
```


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