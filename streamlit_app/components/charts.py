"""Composants de visualisation avec Plotly pour Streamlit"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict


# ------------------------- FONCTIONS EXISTANTES -------------------------

def create_consumption_chart(data: List[Dict], chart_type: str = "bar") -> go.Figure:
    df = pd.DataFrame(data or [])
    if df.empty:
        return create_empty_chart("Aucune donnée de consommation disponible")

    # Vérification colonnes minimales
    if chart_type == "bar":
        if "month_name" not in df.columns or "consumption_m3" not in df.columns:
            return create_empty_chart("Colonnes manquantes pour le graphique de consommation (bar)")
        fig = px.bar(
            df, x='month_name', y='consumption_m3', color='consumption_m3',
            title="Consommation Mensuelle par Point d'Eau",
            labels={'consumption_m3': 'Consommation (m³)', 'month_name': 'Mois'},
            color_continuous_scale='Blues'
        )
    elif chart_type == "line":
        if "date" not in df.columns or "consumption_m3" not in df.columns:
            return create_empty_chart("Colonnes manquantes pour le graphique de consommation (line)")
        fig = px.line(
            df, x='date', y='consumption_m3', color='water_point_name',
            title="Évolution de la Consommation par Point d'Eau",
            labels={'consumption_m3': 'Consommation (m³)', 'date': 'Date'}
        )
    else:  # scatter
        if not {"consumption_m3", "revenue_fcfa"}.issubset(df.columns):
            return create_empty_chart("Colonnes manquantes pour le graphique Consommation vs Revenus")
        fig = px.scatter(
            df, x='consumption_m3', y='revenue_fcfa', color='water_point_name',
            size='consumption_m3', title='Relation Consommation vs Revenus',
            labels={'consumption_m3': 'Consommation (m³)', 'revenue_fcfa': 'Revenus (FCFA)'},
            hover_data=['water_point_name', 'date'] if "date" in df.columns else None
        )

    fig.update_layout(
        height=400,
        showlegend=True if chart_type == "line" else False,
        hovermode='x unified' if chart_type == "bar" else 'closest'
    )
    return fig


def create_revenue_chart(data: List[Dict]) -> go.Figure:
    df = pd.DataFrame(data or [])
    if df.empty or "month_name" not in df.columns or "revenue_fcfa" not in df.columns:
        return create_empty_chart("Aucune donnée de revenus disponible")

    monthly_revenue = df.groupby('month_name')['revenue_fcfa'].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_revenue['month_name'], y=monthly_revenue['revenue_fcfa'],
        name='Revenus Mensuels', marker_color='lightseagreen',
        hovertemplate='<b>%{x}</b><br>Revenus: %{y:,.0f} FCFA<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=monthly_revenue['month_name'], y=monthly_revenue['revenue_fcfa'],
        mode='lines+markers', name='Tendance',
        line=dict(color='orange', width=3), marker=dict(size=8)
    ))
    fig.update_layout(
        title='Évolution des Revenus Mensuels',
        xaxis_title='Mois',
        yaxis_title='Revenus (FCFA)',
        height=400,
        hovermode='x unified'
    )
    return fig


def create_empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=16, color="gray")
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='white', height=400
    )
    return fig


# ------------------------- FONCTIONS SUPPLÉMENTAIRES -------------------------

def create_status_distribution(water_points: List[Dict]) -> go.Figure:
    df = pd.DataFrame(water_points or [])
    if df.empty or "status" not in df.columns:
        return create_empty_chart("Aucune donnée de statut disponible")

    status_counts = df['status'].value_counts()
    colors = {'active': 'green', 'inactive': 'red', 'maintenance': 'orange'}
    bar_colors = [colors.get(status, 'blue') for status in status_counts.index]

    fig = go.Figure(data=[go.Bar(
        x=status_counts.index, y=status_counts.values,
        marker_color=bar_colors, text=status_counts.values,
        textposition='auto'
    )])
    fig.update_layout(
        title="Distribution des Statuts des Points d'Eau",
        xaxis_title="Statut", yaxis_title="Nombre de Points", height=400
    )
    return fig


def create_status_chart(data: List[Dict]) -> go.Figure:
    return create_status_distribution(data)


def create_connection_type_pie(water_points: List[Dict]) -> go.Figure:
    df = pd.DataFrame(water_points or [])
    if df.empty or "connection_type" not in df.columns:
        return create_empty_chart("Aucune donnée sur les types de connexion")

    type_counts = df['connection_type'].value_counts()
    fig = go.Figure(data=[go.Pie(
        labels=type_counts.index, values=type_counts.values, hole=0.4,
        marker_colors=['lightcoral', 'lightskyblue']
    )])
    fig.update_layout(
        title="Répartition par Type de Connexion", height=400, showlegend=True,
        annotations=[dict(text="Points d'Eau", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig


# ------------------------- ALIAS DE COMPATIBILITÉ -------------------------

# On évite de référencer des fonctions inexistantes
create_top_performers_chart = globals().get("create_top_performers_chart", create_empty_chart)
create_anomalies_chart = globals().get("create_anomalies_chart", create_empty_chart)
