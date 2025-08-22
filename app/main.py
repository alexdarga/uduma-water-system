"""Application FastAPI principale - API REST pour Uduma Water Management"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app import crud, models, schemas
from .database import SessionLocal, engine, create_tables

# Créer les tables au démarrage
create_tables()

# Initialiser FastAPI
app = FastAPI(
    title="Uduma Water Management API",
    description="API REST pour la gestion des points d'eau - Projet Uduma",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS pour Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# Routes principales
# ----------------------------
@app.get("/", tags=["Root"])
def read_root():
    """Point d'entrée de l'API"""
    return {
        "message": "Uduma Water Management API",
        "version": "1.0.0",
        "endpoints": {
            "water_points": "/water_points",
            "consumption": "/consumption",
            "kpis": "/analytics/kpis",
            "anomalies": "/analytics/anomalies",
            "docs": "/docs"
        }
    }

# ----------------------------
# Routes Water Points
# ----------------------------
@app.get("/water_points", response_model=List[schemas.WaterPoint], tags=["Water Points"])
def get_water_points(
    commune: Optional[str] = Query(None, description="Filtrer par commune"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    skip: int = Query(0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, description="Nombre maximum d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    return crud.get_water_points(db, commune=commune, status=status, skip=skip, limit=limit)

@app.get("/water_points/{water_point_id}", response_model=schemas.WaterPoint, tags=["Water Points"])
def get_water_point(water_point_id: int, db: Session = Depends(get_db)):
    water_point = crud.get_water_point(db, water_point_id)
    if not water_point:
        raise HTTPException(status_code=404, detail="Point d'eau non trouvé")
    return water_point

@app.post("/water_points", response_model=schemas.WaterPoint, tags=["Water Points"])
def create_water_point(water_point: schemas.WaterPointCreate, db: Session = Depends(get_db)):
    return crud.create_water_point(db, water_point)

@app.put("/water_points/{water_point_id}", response_model=schemas.WaterPoint, tags=["Water Points"])
def update_water_point(water_point_id: int, water_point_update: schemas.WaterPointUpdate, db: Session = Depends(get_db)):
    updated_water_point = crud.update_water_point(db, water_point_id, water_point_update)
    if not updated_water_point:
        raise HTTPException(status_code=404, detail="Point d'eau non trouvé")
    return updated_water_point

# ----------------------------
# Routes Meter Readings / Consumption
# ----------------------------
@app.get("/water_points/{water_point_id}/consumption", tags=["Consumption"])
def get_water_point_consumption(
    water_point_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    water_point = crud.get_water_point(db, water_point_id)
    if not water_point:
        raise HTTPException(status_code=404, detail="Point d'eau non trouvé")
    
    consumption_data = crud.get_water_point_consumption(db, water_point_id, start_date, end_date)
    return {
        "water_point_id": water_point_id,
        "water_point_name": water_point.name,
        "consumption_history": consumption_data
    }

@app.get("/consumption", tags=["Consumption"])
def get_consumption_data(
    commune: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    water_points = crud.get_water_points(db, commune=commune, status=status, limit=1000)
    all_consumption = []
    for wp in water_points:
        all_consumption.extend(crud.get_water_point_consumption(db, wp.id, start_date, end_date))
    
    return {
        "total_records": len(all_consumption),
        "filters_applied": {"commune": commune, "status": status, "start_date": start_date, "end_date": end_date},
        "data": all_consumption
    }

@app.post("/meter_readings", response_model=schemas.MeterReading, tags=["Meter Readings"])
def create_meter_reading(reading: schemas.MeterReadingCreate, db: Session = Depends(get_db)):
    water_point = crud.get_water_point(db, reading.water_point_id)
    if not water_point:
        raise HTTPException(status_code=404, detail="Point d'eau non trouvé")
    return crud.create_meter_reading(db, reading)

# ----------------------------
# Routes Analytics / KPIs
# ----------------------------
@app.get("/analytics/kpis", response_model=schemas.KPIsResponse, tags=["Analytics"])
def get_kpis(db: Session = Depends(get_db)):
    """Récupérer les KPIs (indicateurs clés de performance) du système"""
    return crud.get_kpis(db)

@app.get("/analytics/anomalies", response_model=List[schemas.AnomalyResponse], tags=["Analytics"])
def get_anomalies(db: Session = Depends(get_db)):
    return crud.detect_anomalies(db)

# ----------------------------
# Routes Communes / Statistics
# ----------------------------
@app.get("/communes", tags=["Statistics"])
def get_communes(db: Session = Depends(get_db)):
    water_points = crud.get_water_points(db, limit=1000)
    communes = sorted(set([wp.commune for wp in water_points if wp.commune]))
    return {"communes": communes}

@app.get("/statistics/summary", tags=["Statistics"])
def get_summary_statistics(db: Session = Depends(get_db)):
    water_points = crud.get_water_points(db, limit=1000)
    readings = crud.get_meter_readings(db, limit=10000)
    
    connection_stats = {}
    for wp in water_points:
        conn_type = wp.connection_type
        if conn_type not in connection_stats:
            connection_stats[conn_type] = {"count": 0, "active": 0}
        connection_stats[conn_type]["count"] += 1
        if wp.status == "active":
            connection_stats[conn_type]["active"] += 1
    
    commune_stats = {}
    for wp in water_points:
        commune = wp.commune
        if commune not in commune_stats:
            commune_stats[commune] = {"total": 0, "active": 0}
        commune_stats[commune]["total"] += 1
        if wp.status == "active":
            commune_stats[commune]["active"] += 1
    
    return {
        "connection_type_distribution": connection_stats,
        "commune_distribution": commune_stats,
        "total_readings": len(readings),
        "date_range": {
            "earliest": min([r.reading_date for r in readings]) if readings else None,
            "latest": max([r.reading_date for r in readings]) if readings else None
        }
    }

# ----------------------------
# Route santé / Monitoring
# ----------------------------
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "Uduma Water Management API", "version": "1.0.0"}
