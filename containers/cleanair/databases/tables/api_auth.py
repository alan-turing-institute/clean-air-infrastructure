"""
Tables for API authentication
"""
from sqlalchemy import Column, ForeignKey, String, Integer, Boolean
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from ..base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "api_auth"}

    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    password_hash = Column(String(128))
    email = Column(String(320))
    approved = Column(Boolean, default=0)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        if self.approved:
            s = Serializer('secret', expires_in=expiration)
            return s.dumps({'id': self.id})
        return None

    @staticmethod
    def verify_auth_token(token):
        s = Serializer('secret')
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user
