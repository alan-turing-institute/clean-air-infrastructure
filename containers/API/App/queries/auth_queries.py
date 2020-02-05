"""API database queries related to authentication"""
import logging
from sqlalchemy import func
from cleanair.loggers import get_log_level
from cleanair.decorators import db_query
from cleanair.databases.tables import ModelResult, MetaPoint, User

logging.basicConfig(level=get_log_level(0))


@db_query
def check_user_exists(session, username):
    """Check if an API user exists"""
    return session.query(User).filter(User.username == username)


def create_user(session, username, password, email):
    user = User(username=username, email=email)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return user


def get_user(session, username):

    return session.query(User).filter(User.username == username)
