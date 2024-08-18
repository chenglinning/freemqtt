# Copyright (C) 2024-2034 
# Chenglin Ning, chenglinning@gmain.com
#
import logging

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool

from .singleton import singleton
from .models import Base
from ..server.config import DBCfg

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except:
        raise exc.DisconnectionError()
    
@singleton
class SQLite():
    def __init__(self):
        self.dbengine = None
       
    def createEngine(self):
        if self.dbengine == None:
#           self.dbengine = create_engine(f"sqlite:///./{DBCfg.path}", echo_pool=True)
            self.dbengine = create_engine(f"sqlite:///./{DBCfg.path}")

        if not self.dbengine:
            logging.debug("SQLite connect: Failure")
            
        return self.dbengine

    def getSessionClass(self):
        assert(self.dbengine)
        return scoped_session(sessionmaker(bind=self.dbengine))

    def createTables(self, tblist=None):
        Base.metadata.create_all(self.dbengine, tables=tblist)

    def dropTables(self, tblist=None):
        Base.metadata.drop_all(self.dbengine, tables=tblist)

    def getTables(self):
        return Base.metadata.tables

def getDBSessionClass():
    db = SQLite()
    db.createEngine()
    return db.getSessionClass()

def getDatabaseInstance():
    db = SQLite()
    db.createEngine()
    return db

def getDatabaseEngine():
    db = SQLite()
    db.createEngine()
    return db.dbengine
