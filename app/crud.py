"""Opérations CRUD pour la base de données"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import date, datetime
from . import models, schemas

# -------------------------------
# CRUD pour WaterPoint
# -------------------------------
def get_water_points(
    db: Session, 
    commune: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[models.WaterPoint]:
    """Récupérer la liste des points d'eau avec filtres optionnels"""
    query = db.query(models.WaterPoint)
    if commune:
        query = query.filter(models.WaterPoint.commune == commune)
    if status:
        query = query.filter(models.WaterPoint.status == status)
    return query.offset(skip).limit(limit).all()


def get_water_point(db: Session, water_point_id: int) -> Optional[models.WaterPoint]:
    """Récupérer un point d'eau par son ID"""
    return db.query(models.WaterPoint).filter(models.WaterPoint.id == water_point_id).first()


def create_water_point(db: Session, water_point: schemas.WaterPointCreate) -> models.WaterPoint:
    """Créer un nouveau point d'eau"""
    db_water_point = models.WaterPoint(**water_point.dict())
    db.add(db_water_point)
    db.commit()
    db.refresh(db_water_point)
    return db_water_point


def update_water_point(
    db: Session, 
    water_point_id: int, 
    water_point_update: schemas.WaterPointUpdate
) -> Optional[models.WaterPoint]:
    """Mettre à jour un point d'eau"""
    db_water_point = get_water_point(db, water_point_id)
    if db_water_point:
        update_data = water_point_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_water_point, field, value)
        db.commit()
        db.refresh(db_water_point)
    return db_water_point


# -------------------------------
# CRUD pour MeterReading
# -------------------------------
def get_meter_readings(
    db: Session,
    water_point_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 1000
) -> List[models.MeterReading]:
    """Récupérer les relevés avec filtres"""
    query = db.query(models.MeterReading)
    if water_point_id:
        query = query.filter(models.MeterReading.water_point_id == water_point_id)
    if start_date:
        query = query.filter(models.MeterReading.reading_date >= start_date)
    if end_date:
        query = query.filter(models.MeterReading.reading_date <= end_date)
    return query.order_by(desc(models.MeterReading.reading_date)).offset(skip).limit(limit).all()


def calculate_consumption(
    db: Session, 
    water_point_id: int, 
    current_index: int, 
    current_date: date
) -> float:
    """Calculer la consommation basée sur le relevé précédent"""
    previous_reading = db.query(models.MeterReading)\
        .filter(models.MeterReading.water_point_id == water_point_id)\
        .filter(models.MeterReading.reading_date < current_date)\
        .order_by(desc(models.MeterReading.reading_date))\
        .first()
    if previous_reading:
        return max(0, current_index - previous_reading.meter_index)
    return 0.0


def create_meter_reading(db: Session, reading: schemas.MeterReadingCreate) -> models.MeterReading:
    """Créer un nouveau relevé de compteur"""
    consumption = calculate_consumption(db, reading.water_point_id, reading.meter_index, reading.reading_date)
    db_reading = models.MeterReading(**reading.dict(), consumption_m3=consumption)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading


# -------------------------------
# Analyse & rapports
# -------------------------------
def get_water_point_consumption(
    db: Session, 
    water_point_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[schemas.ConsumptionResponse]:
    """Récupérer la consommation d'un point d'eau au format API"""
    readings = get_meter_readings(db, water_point_id, start_date, end_date, limit=1000)
    consumption_data = []
    for reading in readings:
        water_point = get_water_point(db, reading.water_point_id)
        consumption_data.append(
            schemas.ConsumptionResponse(
                water_point_id=reading.water_point_id,
                water_point_name=water_point.name if water_point else "Unknown",
                month=reading.reading_date.strftime("%Y-%m"),
                consumption_m3=reading.consumption_m3 or 0,
                revenue_fcfa=reading.revenue_fcfa,
                previous_index=None,  # peut être amélioré si besoin
                current_index=reading.meter_index
            )
        )
    return consumption_data


def detect_anomalies(db: Session) -> List[schemas.AnomalyResponse]:
    """Détecter les anomalies dans les relevés"""
    anomalies: List[schemas.AnomalyResponse] = []
    water_points = get_water_points(db)
    for wp in water_points:
        readings = get_meter_readings(db, wp.id, limit=1000)
        if len(readings) < 2:
            continue
        readings_sorted = sorted(readings, key=lambda x: x.reading_date)
        for i in range(1, len(readings_sorted)):
            current = readings_sorted[i]
            previous = readings_sorted[i-1]
            if current.meter_index < previous.meter_index:
                anomalies.append(
                    schemas.AnomalyResponse(
                        water_point_id=wp.id,
                        water_point_name=wp.name,
                        anomaly_type="meter_rollback",
                        description=f"Compteur recule: {previous.meter_index} → {current.meter_index}",
                        reading_date=current.reading_date,
                        severity="high"
                    )
                )
            if current.revenue_fcfa > 0 and (current.consumption_m3 or 0) == 0:
                anomalies.append(
                    schemas.AnomalyResponse(
                        water_point_id=wp.id,
                        water_point_name=wp.name,
                        anomaly_type="revenue_without_consumption",
                        description=f"Revenus ({current.revenue_fcfa} FCFA) sans consommation",
                        reading_date=current.reading_date,
                        severity="medium"
                    )
                )
    return anomalies


def get_kpis(db: Session) -> schemas.KPIsResponse:
    """Calculer les KPIs généraux du système"""
    water_points = get_water_points(db, limit=1000)
    total_points = len(water_points)
    active_points = len([wp for wp in water_points if wp.status == "active"])
    inactive_points = len([wp for wp in water_points if wp.status == "inactive"])
    maintenance_points = len([wp for wp in water_points if wp.status == "maintenance"])
    all_readings = get_meter_readings(db, limit=10000)
    total_consumption = sum([r.consumption_m3 or 0 for r in all_readings])
    total_revenue = sum([r.revenue_fcfa for r in all_readings])
    avg_consumption = total_consumption / total_points if total_points > 0 else 0
    anomalies = detect_anomalies(db)
    return schemas.KPIsResponse(
        total_water_points=total_points,
        active_water_points=active_points,
        inactive_water_points=inactive_points,
        maintenance_water_points=maintenance_points,
        total_monthly_consumption=total_consumption,
        total_monthly_revenue=total_revenue,
        average_consumption_per_point=avg_consumption,
        anomalies_detected=len(anomalies)
    )
