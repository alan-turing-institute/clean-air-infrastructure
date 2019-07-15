import argparse
import requests
import os
import logging
import termcolor
import json

from datetime import timedelta, datetime

from sqlalchemy import Column, String, create_engine, exists, and_
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from geoalchemy2 import Geometry
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pdb
ONE_DAY = timedelta(days=1)

def days(d):
    "Time delta in days"
    return timedelta(days=d)


def green(text):
    return termcolor.colored(text, "green")


def red(text):
    return termcolor.colored(text, "red")
    

def connected_to_internet(url="http://www.google.com/", timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def dict_clean(dictionary):
    """
    Coerce missing keys to 'None'
    """
    for key in dictionary.keys():
        if not dictionary[key]:
            dictionary[key] = None
    return dictionary

def drop_duplicates(data):
    """
    If the data from the api contains duplicates then drop them
    """
    deduped_list = [dict(t) for t in {tuple(d.items()) for d in data}]
    n_dropped = len(deduped_list) - len(data)

    if n_dropped > 0:
        logging.warning("Dropped %s data points", n_dropped)
        return deduped_list
    return data


def str_to_datetime(date_str):
    """
    Get a datetime from a known-format string
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def emptystr_2_none(x):
    """
    Convert empty strings to None
    """

    if isinstance(x, str) and (x == ''):
        return None
    else:
        return x

def map_dict(d1, f):
    """
    Map a function to every item in a dictionary
    """

    d2 = {k: f(v) for k, v in d1.items()}
    return d2


def datetime_floor(dtime):
    """
    Set the time to midnight for a given datetime
    """
    return datetime.combine(dtime, datetime.min.time())


def get_data_range(site, start_date, end_date):
    """
    Get the dates that data is available for a site between start_date and end_date
    If no data is available between these dates returns None
    """ 

    if not start_date:
        get_data_from = datetime_floor(site.DateOpened)
    else:        
        get_data_from = max([datetime_floor(site.DateOpened), datetime_floor(str_to_datetime(start_date))])

    if not end_date:
        if not site.DateClosed:
            get_data_to = datetime.today()
        else:
            get_data_to = min(
                [datetime_floor(datetime.today()), datetime_floor(site.DateClosed)])

    else:
        if not site.DateClosed:
            get_data_to = datetime_floor(str_to_datetime(end_date))
        else:
            # Site is closed to get data until that point
            get_data_to = min(
                [datetime_floor(str_to_datetime(end_date)),
                 datetime_floor(site.DateClosed)]
            )
            

    delta = get_data_to - get_data_from  # Number of days available for a site

    if delta.days < 0:
        return None
    return (get_data_from, get_data_to)


def load_db_info(secret_file):
    """
    Loads database secrets from a json file.
    Check file system is accessable from docker and return database login info
    """

    mount_dir = 'secrets'
    local_dir = './terraform/.secrets/'

    # Check if the following directories exist
    check_secrets_mount = os.path.isdir(mount_dir)
    check_local_dir = os.path.isdir(local_dir)

    secret_fname = None
    if check_secrets_mount:
        logging.info("{} is mounted".format(mount_dir))
        secret_fname = os.path.join(mount_dir, secret_file)

    elif check_local_dir:
        logging.info("{} exists locally".format(check_local_dir))
        secret_fname = os.path.join(local_dir, secret_file)

    else:
        raise FileNotFoundError(
            "Database secrets could not be found. Check that either {} is mounted or {} exists locally".format(mount_dir, local_dir))

    try:
        with open(secret_fname) as f:
            data = json.load(f)
           
        logging.info("Database connection information loaded")

    except FileNotFoundError:
        logging.error(
            "Database secrets could not be found. Ensure secret_file exists")
        raise FileNotFoundError

    return data

def create_connection_string(host, port, dbname, user, password):
    """
    Create a postgres connection string
    """
    connection_string = "postgresql://{}:{}@{}:{}/{}".format(
        user, password, host, port, dbname)
    return connection_string

