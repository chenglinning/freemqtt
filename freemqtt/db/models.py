# Copyright (C) 2024-2034 
# Chenglin Ning, chenglinning@gmain.com
#
import datetime
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "tb_user"
    id = Column("id", String(64), primary_key = True, nullable=False)
    password = Column("password", String(64), nullable=False)
    nickname = Column("nickname", String(128), nullable=True)
    status = Column("status", String(64), nullable=True, default='signout')
    createtime = Column("createtime", DateTime, default=datetime.datetime.now)
    updatetime = Column("updatetime", DateTime, default=datetime.datetime.now)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

class FreemqttApp(Base):
    __tablename__ = "tb_app"
    id = Column("id", String(32), primary_key = True, nullable=False)
    appname = Column("appname", String(64), nullable=False)
    token = Column("token", String(64), nullable=False)
    config = Column("config", Text, nullable=True, default='{}')
    ownerid = Column("ownerid", String(32), ForeignKey("tb_user.id", ondelete="CASCADE"), nullable=False)
    enabled = Column("enabled", Boolean, nullable=False, default=True)

    createtime = Column("createtime", DateTime, default=datetime.datetime.now)
    updatetime = Column("updatetime", DateTime, default=datetime.datetime.now)
    user = relationship("User", backref="apps")

    def __init__(self, *args, **kwargs):
        super(FreemqttApp, self).__init__(*args, **kwargs)
