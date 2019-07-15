import os
import logging
import json
from sqlalchemy import create_engine


def create_connection_string(
        host, port, dbname, user, password, ssl_mode='require'):
    "Create a postgres connection string"
    connection_string = 'postgresql://{}:{}@{}:{}/{}'.format(
        user, password, host, port, dbname)

    return connection_string


def load_db_info():
    "Check file system is accessable from docker and return database login info"

    mount_dir = '/.secrets/'
    secret_file = '.secret.json'

    # Check if the following directories exist
    secret_fname = os.path.join(mount_dir, secret_file)

    try:
        with open(secret_fname) as f:
            data = json.load(f)
        logging.info("Database connection information loaded")

    except FileNotFoundError:
        logging.error(
            "Database secrets could not be found. Ensure secret_file exists")
        raise FileNotFoundError

    return data


def main():

    log_level = logging.INFO

    logging.basicConfig(format=r"%(asctime)s %(levelname)8s: %(message)s",
                        datefmt=r"%Y-%m-%d %H:%M:%S", level=log_level)

    db_info = load_db_info()

    # Connect to the database
    host = db_info['host']
    port = db_info['port']
    dbname = db_info['db_name']
    user = db_info['username']
    ssl_mode = db_info['ssl_mode']
    db_password = db_info['password']

    connection_string = create_connection_string(host=host,
                                                 port=port,
                                                 dbname=dbname,
                                                 user=user,
                                                 password=db_password,
                                                 ssl_mode=ssl_mode)

    logging.info("Installing postGIS on {}".format(host))
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    logging.info("Install complete")


if __name__ == '__main__':

    main()
