# _1_models.py
# makes the table:
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, DateTime
from sqlalchemy.orm import declarative_base

import datetime

Base = declarative_base()

class Phone(Base):
    __tablename__ = 'phones'
    id = Column(Integer, primary_key=True)
    model_name = Column(String, nullable=False, unique=True)
    brand = Column(String, default='Samsung')
    release_date = Column(Date, nullable=True)
    display = Column(Text)
    battery = Column(Integer)
    camera = Column(Text)
    ram = Column(String)
    storage = Column(String)
    price_usd = Column(Numeric(10,2))
    source_url = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow) #gp