# app/models/wild_fire_data.py
from geoalchemy2 import Geography
from sqlalchemy import Column, Integer, Float, DateTime, String
from .base import Base

class WildFireData(Base):
    __tablename__ = 'wildfire_data'
    id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    brightness = Column(Float)  # Typical for MODIS and VIIRS
    scan = Column(Float)
    track = Column(Float)
    acq_date = Column(DateTime, index=True)
    acq_time = Column(String)
    satellite = Column(String)
    confidence = Column(String)
    version = Column(String)  # Changed from Float to String to accommodate values like '6.1NRT'
    bright_t31 = Column(Float)  # Typical for MODIS
    frp = Column(Float)  # Fire Radiative Power
    daynight = Column(String)
    location = Column(Geography(geometry_type='POINT', srid=4326))