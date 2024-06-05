## Installing and Starting PostgreSQL

To install and start PostgreSQL on macOS, you can use Homebrew Services. Below are detailed, step-by-step instructions.

### Step-by-Step Instructions

1. **Install Homebrew:**
   If Homebrew is not already installed on your system, open your terminal and execute the following command:

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

   **Documentation:**
   - [Homebrew Installation](https://brew.sh/)

2. **Install PostgreSQL using Homebrew:**
   With Homebrew installed, install PostgreSQL by running:

   ```bash
   brew install postgresql
   ```

   This command installs the latest version of PostgreSQL available via Homebrew.

   **Documentation:**
   - [PostgreSQL Homebrew Installation](https://formulae.brew.sh/formula/postgresql)

3. **Install Homebrew Services:**
   Homebrew Services is an extension for Homebrew that simplifies the process of starting and stopping services. Install it with:

   ```bash
   brew tap homebrew/services
   ```

   **Documentation:**
   - [Homebrew Services](https://github.com/Homebrew/homebrew-services)

4. **Start PostgreSQL Service:**
   Start PostgreSQL as a service using Homebrew Services:

   ```bash
   brew services start postgresql
   ```

   This command runs PostgreSQL as a background service, which will automatically restart after a reboot.

   **Documentation:**
   - [Starting Services with Homebrew](https://github.com/Homebrew/homebrew-services#readme)

### If You Installed PostgreSQL Using Conda

To set up the PostgreSQL server and users, follow these steps:

1. **Initialize the Database:**

   ```bash
   initdb -D mylocal_db
   ```

2. **Start the PostgreSQL Server:**

   ```bash
   pg_ctl -D mylocal_db -l logfile start
   ```

3. **Create a Database:**

   ```bash
   createdb --owner=${USER} myinner_db
   ```

4. **Start the Server for Future Sessions:**
   When you want to work in this environment again, start the server with:

   ```bash
   pg_ctl -D mylocal_db -l logfile start
   ```

5. **Stop the Server:**
   You can stop the server with:

   ```bash
   pg_ctl -D mylocal_db stop
   ```

## Creating a Local Secrets File

Refer to the [secret file documentation](secretfile.md) for detailed instructions.

In some cases, your default username may be your OS user. Adjust the username in the secrets file if necessary.

## Create a Database on Your Machine

Create a database named `cleanair_test_db` with the following command:

```bash
createdb cleanair_test_db
```

## Create Schema and Roles

To set up the database schema and create roles, follow these steps:

1. **Set the Location of Your Secrets File:**

   ```bash
   export DB_SECRET_FILE=$(pwd)/.secrets/.db_secrets_offline.json
   ```

2. **Configure Database Roles:**
   Run the following command to configure database roles:

   ```bash
   python containers/entrypoints/setup/configure_db_roles.py -s $DB_SECRET_FILE -c configuration/database_role_config/local_database_config.yaml
   ```

### Insert Static Data

**TODO:** Instructions for inserting static data into the server database need to be provided.

### Check the Database Configuration

Verify that everything is configured correctly by running:

```bash
pytest containers/tests/test_database_init --secretfile $DB_SECRET_FILE
```

By following these steps, you will have PostgreSQL installed, configured, and running on your macOS system.
