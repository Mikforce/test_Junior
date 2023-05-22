import uuid
from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    name = Column(String)
    token = Column(String)

    def __init__(self, name, token):
        self.name = name
        self.token = token

class Record(Base):
    __tablename__ = 'records'

    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String)
    url = Column(String)

    def __init__(self, user_id, url):
        self.user_id = user_id
        self.url = url

engine = create_engine('postgresql://your_username:your_password@localhost:5432/your_database_name')
Base.metadata.create_all(engine)