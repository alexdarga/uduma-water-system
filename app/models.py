"""Modèles SQLAlchemy pour la base de données"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base  # ⚠️ Utilise import absolu pour éviter les soucis d'import

class WaterPoint(Base):
    """Modèle pour les points d'eau"""
    __tablename__ = "water_points"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    commune = Column(String(50), nullable=False, index=True)
    village = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    installation_date = Column(Date, nullable=True)
    meter_type = Column(String(50), nullable=True)
    connection_type = Column(String(50), nullable=False)  # "Borne Fontaine" ou "Connexion Privée"
    status = Column(String(20), nullable=False, default="active")  # "active", "inactive", "maintenance"
    created_at = Column(DateTime, server_default=func.now())
    
    # Relations
    readings = relationship("MeterReading", back_populates="water_point", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WaterPoint(name='{self.name}', commune='{self.commune}', status='{self.status}')>"

class MeterReading(Base):
    """Modèle pour les relevés de compteur"""
    __tablename__ = "meter_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    water_point_id = Column(Integer, ForeignKey("water_points.id", ondelete="CASCADE"), nullable=False)
    reading_date = Column(Date, nullable=False, index=True)
    meter_index = Column(Integer, nullable=False)
    revenue_fcfa = Column(Integer, nullable=False, default=0)
    recorded_by = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    consumption_m3 = Column(Float, nullable=True)  # Calculé automatiquement
    consumption_anomaly = Column(Float, nullable=True, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relations
    water_point = relationship("WaterPoint", back_populates="readings")
    
    def __repr__(self):
        return f"<MeterReading(water_point_id={self.water_point_id}, date={self.reading_date}, index={self.meter_index})>"
