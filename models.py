__author__ = 'william'

from sqlalchemy import Column, Integer, String
from database import Base
import json

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)
    password = Column(String(20), unique=False)
    name = Column(String(30), unique=False)
    profile_photo = Column(String(80), unique=False)

    def __init__(self, username=None, password=None, name=None, profile_photo=None):
        self.username = username
        self.password = password
        self.name = name
        self.profile_photo = profile_photo

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)


    def __repr__(self):
        return '<User %r' % (self.username)