# scripts/data_import.py
import pandas as pd
import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db_session, create_tables
from app import models

# -------------------------------
# Nettoyage et préparation
# -------------------------------
def clean_and_prepare_data(df):
    """Nettoie et prépare les données pour l'import"""
    print("🔧 Nettoyage des données...")

    df_clean = df.copy()

    # Conversion des dates
    df_clean['installation_date'] = pd.to_datetime(df_clean['installation_date'], format='%d/%m/%Y', errors='coerce')
    df_clean['reading_date'] = pd.to_datetime(df_clean['reading_date'], format='%d/%m/%Y', errors='coerce')

    # Nettoyage des espaces et valeurs nulles
    string_cols = ['point_name', 'commune', 'village', 'status', 'recorded_by', 'notes']
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
            df_clean[col] = df_clean[col].replace('nan', '')

    # Tri par point d'eau et date
    df_clean = df_clean.sort_values(['point_name', 'reading_date'])

    print(f"✅ {len(df_clean)} lignes nettoyées")
    return df_clean

# -------------------------------
# Calcul des consommations
# -------------------------------
def calculate_consumption(df):
    """Calcule la consommation pour chaque point d'eau"""
    print("📊 Calcul des consommations...")

    df_calc = df.copy()
    df_calc['consumption_m3'] = 0.0
    df_calc['consumption_anomaly'] = False

    for point_name in df_calc['point_name'].unique():
        mask = df_calc['point_name'] == point_name
        point_data = df_calc[mask].sort_values('reading_date')

        consumptions = []
        anomalies = []

        for i in range(len(point_data)):
            if i == 0:
                consumption = 0
                anomaly = False
            else:
                prev_index = point_data.iloc[i-1]['meter_index']
                curr_index = point_data.iloc[i]['meter_index']
                consumption = curr_index - prev_index
                anomaly = (
                    consumption < 0 or
                    consumption > 1000 or
                    (consumption == 0 and point_data.iloc[i]['revenue_fcfa'] > 0)
                )
            consumptions.append(consumption)
            anomalies.append(anomaly)

        df_calc.loc[point_data.index, 'consumption_m3'] = consumptions
        df_calc.loc[point_data.index, 'consumption_anomaly'] = anomalies

    anomaly_count = df_calc['consumption_anomaly'].sum()
    print(f"✅ Consommations calculées - {anomaly_count} anomalies détectées")
    return df_calc

# -------------------------------
# Import des points d’eau
# -------------------------------
def import_water_points(db: Session, df):
    """Importe les points d'eau uniques"""
    print("🚰 Import des points d'eau...")

    water_points_data = df.groupby(['point_name', 'commune', 'village']).first().reset_index()
    water_point_ids = {}
    imported_count = 0

    for _, row in water_points_data.iterrows():
        existing = db.query(models.WaterPoint).filter(
            models.WaterPoint.name == row['point_name'],
            models.WaterPoint.commune == row['commune'],
            models.WaterPoint.village == row['village']
        ).first()

        if not existing:
            water_point = models.WaterPoint(
                name=row['point_name'],
                commune=row['commune'],
                village=row['village'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                installation_date=row['installation_date'].date() if pd.notnull(row['installation_date']) else None,
                meter_type=row['meter_type'],
                connection_type=row['connection_type'],
                status=row['status']
            )
            db.add(water_point)
            db.flush()  # Récupérer l'ID
            water_point_ids[(row['point_name'], row['commune'], row['village'])] = water_point.id
            imported_count += 1
        else:
            water_point_ids[(row['point_name'], row['commune'], row['village'])] = existing.id

    db.commit()
    print(f"✅ {imported_count} nouveaux points d'eau importés, {len(water_points_data) - imported_count} existants")
    return water_point_ids

# -------------------------------
# Import des relevés
# -------------------------------
def import_meter_readings(db: Session, df, water_point_ids):
    """Importe les relevés de compteurs"""
    print("📊 Import des relevés...")

    imported_count = 0
    updated_count = 0

    for _, row in df.iterrows():
        water_point_key = (row['point_name'], row['commune'], row['village'])
        water_point_id = water_point_ids.get(water_point_key)

        if not water_point_id:
            print(f"⚠️ Point d'eau non trouvé: {water_point_key}")
            continue

        existing = db.query(models.MeterReading).filter(
            models.MeterReading.water_point_id == water_point_id,
            models.MeterReading.reading_date == row['reading_date'].date()
        ).first()

        if not existing:
            reading = models.MeterReading(
                water_point_id=water_point_id,
                reading_date=row['reading_date'].date(),
                meter_index=int(row['meter_index']),
                revenue_fcfa=int(row['revenue_fcfa']),
                recorded_by=row['recorded_by'],
                notes=row['notes'] if row['notes'] else '',
                consumption_m3=float(row['consumption_m3']),
                consumption_anomaly=bool(row['consumption_anomaly'])
            )
            db.add(reading)
            imported_count += 1
        else:
            existing.meter_index = int(row['meter_index'])
            existing.revenue_fcfa = int(row['revenue_fcfa'])
            existing.recorded_by = row['recorded_by']
            existing.notes = row['notes'] if row['notes'] else ''
            existing.consumption_m3 = float(row['consumption_m3'])
            existing.consumption_anomaly = bool(row['consumption_anomaly'])
            updated_count += 1

    db.commit()
    print(f"✅ {imported_count} nouveaux relevés importés, {updated_count} mis à jour")

# -------------------------------
# Chargement CSV
# -------------------------------
def load_data_from_csv(csv_file_path):
    """Charge les données depuis le fichier CSV avec gestion des encodages"""
    print(f"📁 Chargement des données depuis: {csv_file_path}")

    encodings_to_try = ["utf-8", "latin-1"]
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(csv_file_path, sep=';', encoding=enc)
            print(f"✅ {len(df)} lignes chargées avec encodage {enc}")
            print(f"📋 Colonnes: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"⚠️ Erreur avec encodage {enc}: {e}")

    print("❌ Échec du chargement du fichier avec tous les encodages testés")
    return None

# -------------------------------
# Main
# -------------------------------
def main():
    print("🚀 Démarrage de l'import des données Uduma")
    print("=" * 50)

    csv_file_path = "data/raw/Uduma_sample_data.csv"
    if not os.path.exists(csv_file_path):
        print(f"❌ Fichier non trouvé: {csv_file_path}")
        return

    df = load_data_from_csv(csv_file_path)
    if df is None:
        return

    df_clean = clean_and_prepare_data(df)
    df_with_consumption = calculate_consumption(df_clean)

    # ✅ Création des tables AVANT l’import
    print("🗄️ Initialisation de la base de données...")
    create_tables()

    db = get_db_session()
    try:
        water_point_ids = import_water_points(db, df_with_consumption)
        import_meter_readings(db, df_with_consumption, water_point_ids)

        print("\n✅ Import terminé avec succès!")
        print("📊 Statistiques finales:")

        total_points = db.query(models.WaterPoint).count()
        total_readings = db.query(models.MeterReading).count()
        anomalies = db.query(models.MeterReading).filter(models.MeterReading.consumption_anomaly == True).count()

        print(f"   - Points d'eau: {total_points}")
        print(f"   - Relevés: {total_readings}")
        print(f"   - Anomalies: {anomalies}")

    except Exception as e:
        print(f"❌ Erreur lors de l'import: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
