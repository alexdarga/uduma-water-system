"""Utilitaires de calculs métier pour l'interface Streamlit"""

import pandas as pd
from typing import Dict, Any
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, date
import calendar

def process_consumption_data(data: List[Dict]) -> pd.DataFrame:
    """Traiter les données de consommation pour l'analyse"""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Convertir les dates
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    df['year'] = df['date'].dt.year
    df['month_name'] = df['date'].dt.strftime('%B %Y')
    
    # S'assurer que les valeurs numériques sont correctes
    df['consumption_m3'] = pd.to_numeric(df['consumption_m3'], errors='coerce').fillna(0)
    df['revenue_fcfa'] = pd.to_numeric(df['revenue_fcfa'], errors='coerce').fillna(0)
    
    return df

def calculate_monthly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Calculer les agrégats mensuels"""
    if df.empty:
        return pd.DataFrame()
    
    monthly_agg = df.groupby(['month_name', 'month']).agg({
        'consumption_m3': 'sum',
        'revenue_fcfa': 'sum',
        'water_point_id': 'nunique'
    }).reset_index()
    
    monthly_agg = monthly_agg.sort_values('month')
    monthly_agg.columns = ['Month', 'Period', 'Total Consumption (m³)', 'Total Revenue (FCFA)', 'Active Points']
    
    return monthly_agg

def calculate_point_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Calculer les performances par point d'eau"""
    if df.empty:
        return pd.DataFrame()
    
    point_perf = df.groupby(['water_point_name', 'water_point_id']).agg({
        'consumption_m3': ['sum', 'mean', 'count'],
        'revenue_fcfa': ['sum', 'mean'],
        'date': ['min', 'max']
    }).reset_index()
    
    # Aplatir les colonnes multi-niveau
    point_perf.columns = [
        'Point Name', 'Point ID', 
        'Total Consumption', 'Avg Monthly Consumption', 'Readings Count',
        'Total Revenue', 'Avg Monthly Revenue',
        'First Reading', 'Last Reading'
    ]
    
    # Calculer la durée en mois
    point_perf['Months Active'] = (
        (point_perf['Last Reading'] - point_perf['First Reading']).dt.days / 30.44
    ).round(1)
    
    return point_perf.sort_values('Total Revenue', ascending=False)

def detect_consumption_anomalies(df: pd.DataFrame, threshold_std: float = 2.0) -> List[Dict]:
    """Détecter les anomalies de consommation statistiques"""
    anomalies = []
    
    if df.empty:
        return anomalies
    
    # Grouper par point d'eau
    for point_id in df['water_point_id'].unique():
        point_data = df[df['water_point_id'] == point_id].copy()
        point_name = point_data['water_point_name'].iloc[0]
        
        if len(point_data) < 3:  # Besoin d'au moins 3 points pour calculer les anomalies
            continue
            
        consumption = point_data['consumption_m3'].values
        mean_consumption = np.mean(consumption)
        std_consumption = np.std(consumption)
        
        if std_consumption == 0:  # Éviter la division par zéro
            continue
        
        # Détecter les valeurs aberrantes
        z_scores = np.abs((consumption - mean_consumption) / std_consumption)
        anomaly_indices = np.where(z_scores > threshold_std)[0]
        
        for idx in anomaly_indices:
            row = point_data.iloc[idx]
            anomalies.append({
                'water_point_id': int(point_id),
                'water_point_name': point_name,
                'anomaly_type': 'statistical_outlier',
                'description': f"Consommation anormale: {row['consumption_m3']:.1f} m³ (Z-score: {z_scores[idx]:.2f})",
                'reading_date': row['date'].date(),
                'severity': 'high' if z_scores[idx] > 3 else 'medium',
                'value': float(row['consumption_m3']),
                'expected_range': f"{mean_consumption - 2*std_consumption:.1f} - {mean_consumption + 2*std_consumption:.1f} m³"
            })
    
    return anomalies

def calculate_efficiency_metrics(df: pd.DataFrame) -> Dict:
    """Calculer les métriques d'efficacité"""
    if df.empty:
        return {}
    
    total_consumption = df['consumption_m3'].sum()
    total_revenue = df['revenue_fcfa'].sum()
    active_points = df['water_point_id'].nunique()
    
    # Revenue per m³
    revenue_per_m3 = total_revenue / total_consumption if total_consumption > 0 else 0
    
    # Consumption per point
    avg_consumption_per_point = total_consumption / active_points if active_points > 0 else 0
    
    # Revenue per point
    avg_revenue_per_point = total_revenue / active_points if active_points > 0 else 0
    
    return {
        'total_consumption_m3': round(total_consumption, 2),
        'total_revenue_fcfa': int(total_revenue),
        'active_points': active_points,
        'revenue_per_m3': round(revenue_per_m3, 2),
        'avg_consumption_per_point': round(avg_consumption_per_point, 2),
        'avg_revenue_per_point': int(avg_revenue_per_point)
    }

def format_number(value: float, unit: str = "") -> str:
    """Formater les nombres pour l'affichage"""
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M {unit}"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K {unit}"
    else:
        return f"{value:.1f} {unit}"

def calculate_growth_rate(current: float, previous: float) -> float:
    """Calculer le taux de croissance en pourcentage"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100

def get_color_scale(value: float, min_val: float, max_val: float) -> str:
    """Générer une couleur basée sur une échelle"""
    if max_val == min_val:
        return "#2E86AB"
    
    normalized = (value - min_val) / (max_val - min_val)
    
    # Échelle de couleur du rouge au vert
    if normalized <= 0.5:
        # Rouge à jaune
        r = 255
        g = int(255 * (normalized * 2))
        b = 0
    else:
        # Jaune à vert
        r = int(255 * (2 - normalized * 2))
        g = 255
        b = 0
    
    return f"rgb({r}, {g}, {b})"

def prepare_chart_data(df: pd.DataFrame, chart_type: str) -> Dict:
    """Préparer les données pour différents types de graphiques"""
    if df.empty:
        return {}
    
    if chart_type == "monthly_consumption":
        monthly_data = df.groupby('month_name')['consumption_m3'].sum().reset_index()
        return {
            'labels': monthly_data['month_name'].tolist(),
            'data': monthly_data['consumption_m3'].tolist(),
            'title': 'Consommation Mensuelle (m³)'
        }
    
    elif chart_type == "monthly_revenue":
        monthly_data = df.groupby('month_name')['revenue_fcfa'].sum().reset_index()
        return {
            'labels': monthly_data['month_name'].tolist(),
            'data': monthly_data['revenue_fcfa'].tolist(),
            'title': 'Revenus Mensuels (FCFA)'
        }
    
    elif chart_type == "top_points":
        top_points = df.groupby('water_point_name')['consumption_m3'].sum().nlargest(10).reset_index()
        return {
            'labels': top_points['water_point_name'].tolist(),
            'data': top_points['consumption_m3'].tolist(),
            'title': 'Top 10 Points d\'Eau par Consommation'
        }
    
    elif chart_type == "commune_distribution":
        if 'commune' in df.columns:
            commune_data = df.groupby('commune')['consumption_m3'].sum().reset_index()
            return {
                'labels': commune_data['commune'].tolist(),
                'data': commune_data['consumption_m3'].tolist(),
                'title': 'Répartition par Commune'
            }
    
    return {}

def generate_insights(df: pd.DataFrame, kpis: Dict) -> List[str]:
    """Générer des insights automatiques basés sur les données"""
    insights = []
    
    if df.empty or not kpis:
        return ["Aucune donnée disponible pour générer des insights."]
    
    # Insight sur les points d'eau actifs
    total_points = kpis.get('total_water_points', 0)
    active_points = kpis.get('active_water_points', 0)
    if total_points > 0:
        active_percentage = (active_points / total_points) * 100
        if active_percentage >= 90:
            insights.append(f"✅ Excellent taux d'activité: {active_percentage:.1f}% des points d'eau sont actifs")
        elif active_percentage >= 70:
            insights.append(f"⚠️ Taux d'activité modéré: {active_percentage:.1f}% des points d'eau sont actifs")
        else:
            insights.append(f"🔴 Taux d'activité faible: {active_percentage:.1f}% des points d'eau sont actifs")
    
    # Insight sur la consommation moyenne
    avg_consumption = kpis.get('average_consumption_per_point', 0)
    if avg_consumption > 100:
        insights.append(f"💧 Forte consommation moyenne: {avg_consumption:.1f} m³ par point d'eau")
    elif avg_consumption > 50:
        insights.append(f"💧 Consommation moyenne normale: {avg_consumption:.1f} m³ par point d'eau")
    else:
        insights.append(f"💧 Faible consommation moyenne: {avg_consumption:.1f} m³ par point d'eau")
    
    # Insight sur les anomalies
    anomalies_count = kpis.get('anomalies_detected', 0)
    if anomalies_count == 0:
        insights.append("✅ Aucune anomalie détectée dans les relevés")
    elif anomalies_count <= 2:
        insights.append(f"⚠️ {anomalies_count} anomalie(s) détectée(s) - surveillance requise")
    else:
        insights.append(f"🔴 {anomalies_count} anomalies détectées - investigation urgente nécessaire")
    
    # Insight sur les revenus
    total_revenue = kpis.get('total_monthly_revenue', 0)
    if total_revenue > 100000:
        insights.append(f"💰 Bons revenus générés: {format_number(total_revenue, 'FCFA')}")
    else:
        insights.append(f"💰 Revenus modestes: {format_number(total_revenue, 'FCFA')}")
    
    return insights

def calculate_kpis(consumption_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculer des indicateurs clés de performance (KPIs) 
    à partir des données de consommation.
    """
    if consumption_data.empty:
        return {
            "total_volume": 0,
            "total_revenue": 0,
            "avg_consumption": 0,
            "nb_points": 0
        }
    
    total_volume = consumption_data["volume"].sum() if "volume" in consumption_data else 0
    total_revenue = consumption_data["revenue"].sum() if "revenue" in consumption_data else 0
    avg_consumption = consumption_data["volume"].mean() if "volume" in consumption_data else 0
    nb_points = consumption_data["point_id"].nunique() if "point_id" in consumption_data else 0

    return {
        "total_volume": total_volume,
        "total_revenue": total_revenue,
        "avg_consumption": avg_consumption,
        "nb_points": nb_points
    }

# -------------------------------------------------------------------
# Aliases pour compatibilité avec app.py
# -------------------------------------------------------------------
calculate_monthly_consumption = calculate_monthly_aggregates
detect_anomalies = detect_consumption_anomalies
