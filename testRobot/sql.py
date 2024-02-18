from sqlalchemy import create_engine, Column, String, Integer, BigInteger, DateTime, DECIMAL, SmallInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

import pymysql

# 定义映射类的基类
Base = declarative_base()


# 定义UsePhone映射类
class UsePhone(Base):
    __tablename__ = 'use_phone'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(String(64))
    use_vx_user_id = Column(String(256))
    type = Column(SmallInteger)
    num = Column(Integer)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    money = Column(DECIMAL(10, 2))
    my_wxid = Column(String(256))


# 定义User映射类
class User(Base):
    __tablename__ = 'user'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    to_wxid = Column(String(256))
    credits = Column(DECIMAL(10, 2))
    is_first = Column(SmallInteger)
    my_wxid = Column(String(256))

class Phone(Base):
    __tablename__ = 'phone'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user = Column(String(256), nullable=True, comment='账号')
    password = Column(String(256), nullable=True, comment='密码')
    my_wxid = Column(String(256), nullable=True, comment='机器人微信id')
    type = Column(SmallInteger, nullable=True, comment='平台id: 1豪猪')


pymysql.install_as_MySQLdb()


