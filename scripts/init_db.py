"""Script d'import des données CSV vers la base de données"""

import sys
import os
import pandas as pd
from datetime import datetime, date
import glob

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import WaterPoint, MeterReading
from app.crud import calculate_consumption

def clean_numeric_value(value):
    """Nettoyer et convertir une valeur numérique"""
    if pd.isna(value) or value == '':
        return 0
    try:
        # Nettoyer les espaces et convertir
        cleaned = str(value).strip().replace(' ', '')
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0

def parse_date(date_str):
    """Parser une date depuis différents formats"""
    if pd.isna(date_str) or date_str == '':
        return None
    
    # Formats possibles
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt).date()
        except ValueError:
            continue
    
    # Si aucun format ne marche, retourner None
    print(f"⚠️ Format de date non reconnu: {date_str}")
    return None

def import_sample_data():
    """Importer des données d'exemple si aucun CSV n'est trouvé"""
    print("📊 Création de données d'exemple...")
    
    db = SessionLocal()
    try:
        # Données d'exemple basées sur l'analyse fournie
        sample_water_points = [
            {
                "name": "Borne Fontaine Kita",
                "commune": "Kita",
                "village": "Centre",
                "connection_type": "Borne Fontaine",
                "status": "active",
                "latitude": 13.0336,
                "longitude": -9.4890
            },
            {
                "name": "Borne Fontaine Pimperna", 
                "commune": "Pimperna",
                "village": "Centre",
                "connection_type": "Borne Fontaine",
                "status": "maintenance",
                "latitude": 12.8547,
                "longitude": -8.9876
            },
            {
                "name": "Borne Fontaine Blendio",
                "commune": "Blendio", 
                "village": "Centre",
                "connection_type": "Borne Fontaine",
                "status": "inactive",
                "latitude": 12.7123,
                "longitude": -9.1234
            },
            {
                "name": "Connexion Privée Bamako Sud",
                "commune": "Bamako",
                "village": "Sud",
                "connection_type": "Connexion Privée",
                "status": "active",
                "latitude": 12.6392,
                "longitude": -8.0029
            },
            {
                "name": "Connexion Privée Bamako Nord",
                "commune": "Bamako",
                "village": "Nord", 
                "connection_type": "Connexion Privée",
                "status": "active",
                "latitude": 12.6703,
                "longitude": -7.9922
            }
        ]
        
        # Créer les points d'eau
        created_points = []
        for wp_data in sample_water_points:
            wp = WaterPoint(**wp_data)
            db.add(wp)
            db.commit()
            db.refresh(wp)
            created_points.append(wp)
            print(f"✅ Point d'eau créé: {wp.name}")
        
        # Créer des relevés d'exemple pour chaque point d'eau
        sample_readings = []
        months = ['2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', '2024-05-01', '2024-06-01', '2024-07-01']
        
        for wp in created_points:
            base_index = 10000
            for i, month_str in enumerate(months):
                month_date = datetime.strptime(month_str, '%Y-%m-%d').date()
                
                # Simuler différents scénarios
                if wp.name == "Borne Fontaine Blendio" and i > 1:
                    # Point inactif - pas de relevés après février
                    continue
                elif wp.name == "Borne Fontaine Pimperna" and 3 <= i <= 4:
                    # En maintenance en avril-mai
                    consumption = 10  # Consommation réduite
                    revenue = 2000
                elif wp.name == "Borne Fontaine Kita" and i == 6:
                    # Anomalie - compteur recule en juillet
                    consumption = -37  # Compteur recule
                    revenue = 8500
                else:
                    # Consommation normale
                    if wp.connection_type == "Borne Fontaine":
                        consumption = 150 + (i * 25)
                        revenue = 8000 + (i * 500)
                    else:  # Connexion Privée
                        consumption = 75 + (i * 15)
                        revenue = 12000 + (i * 800)
                
                current_index = base_index + sum([150 + (j * 25) for j in range(i+1)])
                if wp.name == "Borne Fontaine Kita" and i == 6:
                    current_index = base_index + sum([150 + (j * 25) for j in range(i)]) - 37
                
                reading = MeterReading(
                    water_point_id=wp.id,
                    reading_date=month_date,
                    meter_index=current_index,
                    revenue_fcfa=max(0, revenue),
                    consumption_m3=max(0, consumption),
                    recorded_by="System Import"
                )
                
                db.add(reading)
                sample_readings.append(reading)
        
        db.commit()
        print(f"✅ {len(sample_readings)} relevés créés")
        
        return len(created_points), len(sample_readings)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import des données d'exemple: {e}")
        db.rollback()
        return 0, 0
    finally:
        db.close()

def import_csv_data():
    """Importer les données depuis des fichiers CSV"""
    print("🔍 Recherche de fichiers CSV dans data/raw/...")
    
    # Chercher des fichiers CSV
    csv_files = glob.glob("data/raw/*.csv")
    
    if not csv_files:
        print("📂 Aucun fichier CSV trouvé dans data/raw/")
        print("💡 Utilisation des données d'exemple...")
        return import_sample_data()
    
    print(f"📁 Fichiers CSV trouvés: {csv_files}")
    
    db = SessionLocal()
    total_points = 0
    total_readings = 0
    
    try:
        for csv_file in csv_files:
            print(f"\n📊 Traitement de {csv_file}...")
            
            try:
                df = pd.read_csv(csv_file)
                print(f"📋 {len(df)} lignes trouvées")
                
                # Analyser la structure du CSV
                print(f"🔍 Colonnes: {list(df.columns)}")
                
                # Adapter selon la structure de vos données
                # Exemple d'import - à adapter selon votre CSV
                for _, row in df.iterrows():
                    # Essayer de créer un point d'eau (adapter les noms de colonnes)
                    try:
                        point_name = row.get('name', row.get('point_name', f"Point {total_points + 1}"))
                        commune = row.get('commune', row.get('location', 'Inconnu'))
                        
                        # Vérifier si le point d'eau existe déjà
                        existing_point = db.query(WaterPoint).filter(
                            WaterPoint.name == point_name
                        ).first()
                        
                        if not existing_point:
                            wp = WaterPoint(
                                name=point_name,
                                commune=commune,
                                village=row.get('village', ''),
                                connection_type=row.get('connection_type', 'Borne Fontaine'),
                                status=row.get('status', 'active'),
                                latitude=pd.to_numeric(row.get('latitude', 0), errors='coerce'),
                                longitude=pd.to_numeric(row.get('longitude', 0), errors='coerce')
                            )
                            db.add(wp)
                            db.commit()
                            db.refresh(wp)
                            total_points += 1
                            print(f"✅ Point créé: {point_name}")
                        else:
                            wp = existing_point
                        
                        # Ajouter un relevé si les données sont présentes
                        if 'meter_index' in row and pd.notna(row['meter_index']):
                            reading_date = parse_date(row.get('reading_date', '2024-01-01'))
                            if reading_date:
                                consumption = calculate_consumption(
                                    db, wp.id, 
                                    clean_numeric_value(row['meter_index']), 
                                    reading_date
                                )
                                
                                reading = MeterReading(
                                    water_point_id=wp.id,
                                    reading_date=reading_date,
                                    meter_index=clean_numeric_value(row['meter_index']),
                                    revenue_fcfa=clean_numeric_value(row.get('revenue_fcfa', 0)),
                                    consumption_m3=consumption,
                                    recorded_by="CSV Import"
                                )
                                db.add(reading)
                                total_readings += 1
                        
                    except Exception as e:
                        print(f"⚠️ Erreur sur la ligne: {e}")
                        continue
                
                db.commit()
                
            except Exception as e:
                print(f"❌ Erreur lors du traitement de {csv_file}: {e}")
                continue
        
        if total_points == 0 and total_readings == 0:
            print("⚠️ Aucune donnée importée depuis les CSV")
            print("💡 Import des données d'exemple...")
            return import_sample_data()
        
        return total_points, total_readings
        
    except Exception as e:
        print(f"❌ Erreur générale lors de l'import: {e}")
        db.rollback()
        return 0, 0
    finally:
        db.close()

def main():
    """Fonction principale d'import"""
    print("=== UDUMA WATER MANAGEMENT - IMPORT DE DONNÉES ===")
    
    try:
        points_created, readings_created = import_csv_data()
        
        print(f"\n📊 RÉSUMÉ DE L'IMPORT:")
        print(f"   • Points d'eau créés: {points_created}")
        print(f"   • Relevés créés: {readings_created}")
        
        if points_created > 0 or readings_created > 0:
            print("\n🎉 Import terminé avec succès!")
            print("📝 Prochaine étape: python run.py")
        else:
            print("\n❌ Aucune donnée importée")
            
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()