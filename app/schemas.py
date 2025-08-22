"""Schémas Pydantic pour la validation des données API"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

# -------------------------------
# Schémas pour WaterPoint
# -------------------------------
class WaterPointBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    commune: str = Field(..., min_length=1, max_length=50)
    village: Optional[str] = Field(None, max_length=50)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    installation_date: Optional[date] = None
    meter_type: Optional[str] = Field(None, max_length=50)
    connection_type: str = Field(..., pattern="^(Borne Fontaine|Connexion Privée)$")
    status: str = Field(default="active", pattern="^(active|inactive|maintenance)$")

class WaterPointCreate(WaterPointBase):
    pass

class WaterPointUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    commune: Optional[str] = Field(None, min_length=1, max_length=50)
    village: Optional[str] = Field(None, max_length=50)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    installation_date: Optional[date] = None
    meter_type: Optional[str] = Field(None, max_length=50)
    connection_type: Optional[str] = Field(None, pattern="^(Borne Fontaine|Connexion Privée)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|maintenance)$")

class WaterPoint(WaterPointBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------
# Schémas pour MeterReading
# -------------------------------
class MeterReadingBase(BaseModel):
    reading_date: date
    meter_index: int = Field(..., ge=0)
    revenue_fcfa: int = Field(default=0, ge=0)
    recorded_by: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    consumption_m3: Optional[float] = None  # ajouté ici pour cohérence

class MeterReadingCreate(MeterReadingBase):
    water_point_id: int

class MeterReadingUpdate(BaseModel):
    reading_date: Optional[date] = None
    meter_index: Optional[int] = Field(None, ge=0)
    revenue_fcfa: Optional[int] = Field(None, ge=0)
    recorded_by: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    consumption_m3: Optional[float] = None

class MeterReading(MeterReadingBase):
    id: int
    water_point_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------
# Schéma pour WaterPoint avec ses relevés
# -------------------------------
class WaterPointWithReadings(WaterPoint):
    readings: List[MeterReading] = []

# -------------------------------
# Schémas pour les réponses API
# -------------------------------
class ConsumptionResponse(BaseModel):
    water_point_id: int
    water_point_name: str
    month: str
    consumption_m3: float
    revenue_fcfa: int
    previous_index: Optional[int]
    current_index: int

class KPIsResponse(BaseModel):
    total_water_points: int
    active_water_points: int
    inactive_water_points: int
    maintenance_water_points: int
    total_monthly_consumption: float
    total_monthly_revenue: int
    average_consumption_per_point: float
    anomalies_detected: int

class AnomalyResponse(BaseModel):
    water_point_id: int
    water_point_name: str
    anomaly_type: str
    description: str
    reading_date: date
    severity: str = Field(..., pattern="^(low|medium|high)$")
