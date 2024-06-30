# app/models/harmonized_landsat_sentinel_data.py
from geoalchemy2 import Geography
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from .base import Base

class HarmonizedLandsatSentinelData(Base):
    __tablename__ = 'harmonized_landsat_sentinel_data'
    id = Column(Integer, primary_key=True)
    place_id = Column(Integer, ForeignKey('places.id', ondelete="CASCADE"), nullable=True)
    
    # Utiliza una cadena de texto para referirse a la clase relacionada
    place = relationship("Place", back_populates="satellite_data")
    
    capture_date = Column(DateTime, index=True)
    location = Column(Geography(geometry_type='POINT', srid=4326))

    b01_coastal_aerosol = Column(Float)
    b02_blue = Column(Float)
    b03_green = Column(Float)
    b04_red = Column(Float)
    b05_nir = Column(Float)
    b06_swir1 = Column(Float)
    b07_swir2 = Column(Float)
    b08_nir_broad = Column(Float)
    b8a_nir_narrow = Column(Float)
    b09_water_vapor = Column(Float)
    b10_cirrus = Column(Float)
    b11_swir1 = Column(Float)
    b12_swir2 = Column(Float)
    ndvi = Column(Float)
    
    additional_data = Column(JSONB)  # Stores additional data like SAA, SZA, VAA, VZA, etc.