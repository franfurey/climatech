# app/models/place.py
from geoalchemy2 import Geography
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String
from .base import Base

class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    location = Column(Geography(geometry_type='POLYGON', srid=4326), index=True)
    
    # Utiliza una cadena de texto para referirse a la clase relacionada
    satellite_data = relationship("HarmonizedLandsatSentinelData", back_populates="place", cascade="all, delete")