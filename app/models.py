# app/models.py
from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geography
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    location = Column(Geography(geometry_type='POLYGON', srid=4326), index=True)