# streamlit_app/components/javascript_components.py
import streamlit as st
import json
from typing import List, Dict, Any

def render_interactive_map(water_points_data: List[Dict], height: int = 500):
    """
    Rendu d'une carte interactive avec JavaScript et Leaflet
    Intègre Python et JavaScript comme requis
    """
    if not water_points_data:
        st.info("Aucun point d'eau à afficher sur la carte")
        return
    
    # Préparer les données pour JavaScript
    map_data = []
    for point in water_points_data:
        map_data.append({
            "id": point.get("id", 0),
            "name": point["name"],
            "lat": point["latitude"],
            "lng": point["longitude"],
            "commune": point["commune"],
            "village": point.get("village", ""),
            "status": point["status"],
            "connection_type": point["connection_type"],
            "installation_date": str(point.get("installation_date", "")),
            "meter_type": point.get("meter_type", "")
        })
    
    # Template HTML + JavaScript
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Carte Interactive Uduma</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ height: {height}px; width: 100%; }}
            .legend {{
                background: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            .legend h4 {{
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: bold;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 5px 0;
            }}
            .legend-color {{
                width: 16px;
                height: 16px;
                border-radius: 50%;
                margin-right: 8px;
                border: 2px solid white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }}
            .popup-title {{
                font-weight: bold;
                font-size: 14px;
                color: #2E86AB;
                margin-bottom: 8px;
            }}
            .popup-info {{
                margin: 4px 0;
                font-size: 12px;
            }}
            .popup-status {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                color: white;
                margin: 4px 0;
            }}
            .status-active {{ background-color: #4CAF50; }}
            .status-inactive {{ background-color: #F44336; }}
            .status-maintenance {{ background-color: #FF9800; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // Configuration de la carte
            const mapConfig = {{
                center: [11.3, -6.5],
                zoom: 8,
                minZoom: 6,
                maxZoom: 18
            }};
            
            // Données des points d'eau (Python vers JavaScript)
            const waterPointsData = {json.dumps(map_data, ensure_ascii=False)};
            
            // Initialiser la carte Leaflet
            const map = L.map('map').setView(mapConfig.center, mapConfig.zoom);
            
            // Ajouter les tuiles de base
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: mapConfig.maxZoom
            }}).addTo(map);
            
            // Fonction pour obtenir la couleur selon le statut
            function getStatusColor(status) {{
                const colors = {{
                    'active': '#4CAF50',
                    'inactive': '#F44336',
                    'maintenance': '#FF9800'
                }};
                return colors[status] || '#9E9E9E';
            }}
            
            // Fonction pour obtenir l'icône selon le type de connexion
            function getConnectionIcon(connectionType) {{
                return connectionType === 'Borne Fontaine' ? '🚰' : '🏠';
            }}
            
            // Fonction pour créer le contenu du popup
            function createPopupContent(point) {{
                const statusClass = `status-${{point.status}}`;
                return `
                    <div class="popup-title">
                        ${{getConnectionIcon(point.connection_type)}} ${{point.name}}
                    </div>
                    <div class="popup-info">
                        <strong>Commune:</strong> ${{point.commune}}
                    </div>
                    <div class="popup-info">
                        <strong>Village:</strong> ${{point.village}}
                    </div>
                    <div class="popup-info">
                        <strong>Type:</strong> ${{point.connection_type}}
                    </div>
                    <div class="popup-info">
                        <strong>Type compteur:</strong> ${{point.meter_type}}
                    </div>
                    <div class="popup-info">
                        <strong>Installation:</strong> ${{point.installation_date}}
                    </div>
                    <div class="popup-info">
                        <span class="popup-status ${{statusClass}}">
                            ${{point.status.toUpperCase()}}
                        </span>
                    </div>
                `;
            }}
            
            // Ajouter les marqueurs pour chaque point d'eau
            const markers = [];
            waterPointsData.forEach(function(point) {{
                const color = getStatusColor(point.status);
                
                const marker = L.circleMarker([point.lat, point.lng], {{
                    radius: 8,
                    fillColor: color,
                    color: 'white',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                
                marker.bindPopup(createPopupContent(point), {{
                    maxWidth: 300,
                    className: 'custom-popup'
                }});
                
                marker.on('mouseover', function() {{
                    this.setStyle({{ radius: 12, weight: 3 }});
                }});
                
                marker.on('mouseout', function() {{
                    this.setStyle({{ radius: 8, weight: 2 }});
                }});
                
                markers.push(marker);
            }});
            
            // Créer la légende
            const legend = L.control({{ position: 'bottomright' }});
            legend.onAdd = function(map) {{
                const div = L.DomUtil.create('div', 'legend');
                div.innerHTML = `
                    <h4>🚰 Points d'Eau</h4>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #4CAF50;"></div>
                        <span>Actif (${{waterPointsData.filter(p => p.status === 'active').length}})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #FF9800;"></div>
                        <span>Maintenance (${{waterPointsData.filter(p => p.status === 'maintenance').length}})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #F44336;"></div>
                        <span>Inactif (${{waterPointsData.filter(p => p.status === 'inactive').length}})</span>
                    </div>
                    <hr style="margin: 10px 0;">
                    <div class="legend-item">
                        <span>🚰 Borne Fontaine (${{waterPointsData.filter(p => p.connection_type === 'Borne Fontaine').length}})</span>
                    </div>
                    <div class="legend-item">
                        <span>🏠 Connexion Privée (${{waterPointsData.filter(p => p.connection_type === 'Connexion Privée').length}})</span>
                    </div>
                `;
                return div;
            }};
            legend.addTo(map);
            
            if (waterPointsData.length > 0) {{
                const group = new L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }}
            
            window.focusOnPoint = function(pointId) {{
                const point = waterPointsData.find(p => p.id === pointId);
                if (point) {{
                    map.setView([point.lat, point.lng], 15);
                    const marker = markers.find(m => m.getLatLng().lat === point.lat && m.getLatLng().lng === point.lng);
                    if (marker) marker.openPopup();
                }}
            }};
            
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'streamlit:componentReady') {{
                    window.parent.postMessage({{
                        type: 'streamlit:componentValue',
                        value: {{
                            totalPoints: waterPointsData.length,
                            activePoints: waterPointsData.filter(p => p.status === 'active').length,
                            mapBounds: map.getBounds()
                        }}
                    }}, '*');
                }}
            }});
            
            console.log('Carte Uduma chargée avec', waterPointsData.length, 'points d\\'eau');
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(html_template, height=height + 50)

def render_interactive_dashboard(kpis_data: Dict, consumption_data: List[Dict]):
    """
    Tableau de bord interactif avec Chart.js
    """
    if not kpis_data or not consumption_data:
        st.error("Données insuffisantes pour le tableau de bord")
        return
    
    monthly_data = kpis_data.get('monthly_trends', [])
    consumption_summary = consumption_data[:10]
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Dashboard Interactif Uduma</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .dashboard-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 1200px; margin: 0 auto; }}
            .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .chart-title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #2E86AB; text-align: center; }}
            .stats-container {{ display: flex; justify-content: space-around; margin-bottom: 20px; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stat-item {{ text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #2E86AB; }}
            .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
            canvas {{ max-height: 300px !important; }}
        </style>
    </head>
    <body>
        <div class="stats-container">
            <div class="stat-item">
                <div class="stat-value" id="totalPoints">{kpis_data.get('total_water_points', 0)}</div>
                <div class="stat-label">Points d'eau</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="activePoints">{kpis_data.get('active_points', 0)}</div>
                <div class="stat-label">Actifs</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="totalRevenue">{kpis_data.get('total_revenue', 0):,.0f}</div>
                <div class="stat-label">Revenus (FCFA)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="anomalyRate">{kpis_data.get('anomaly_rate', 0):.1f}%</div>
                <div class="stat-label">Anomalies</div>
            </div>
        </div>
        
        <div class="dashboard-container">
            <div class="chart-container">
                <div class="chart-title">📈 Évolution Mensuelle des Revenus</div>
                <canvas id="revenueChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">🚰 Top 10 Consommation</div>
                <canvas id="consumptionChart"></canvas>
            </div>
        </div>
        
        <script>
            const monthlyData = {json.dumps(monthly_data)};
            const consumptionData = {json.dumps(consumption_summary)};
            const colors = {{ primary: '#2E86AB', secondary: '#A23B72', success: '#4CAF50', warning: '#FF9800', danger: '#F44336' }};
            
            const revenueCtx = document.getElementById('revenueChart').getContext('2d');
            const revenueChart = new Chart(revenueCtx, {{
                type: 'line',
                data: {{
                    labels: monthlyData.map(d => `Mois ${{d.month}}`),
                    datasets: [{{
                        label: 'Revenus (FCFA)',
                        data: monthlyData.map(d => d.monthly_revenue),
                        borderColor: colors.primary,
                        backgroundColor: colors.primary + '20',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});
            
            const consumptionCtx = document.getElementById('consumptionChart').getContext('2d');
            const consumptionChart = new Chart(consumptionCtx, {{
                type: 'bar',
                data: {{
                    labels: consumptionData.map(d => d.water_point_name.substring(0, 20) + '...'),
                    datasets: [{{
                        label: 'Consommation (m³)',
                        data: consumptionData.map(d => d.total_consumption),
                        backgroundColor: consumptionData.map(d => d.connection_type === 'Borne Fontaine' ? colors.primary : colors.secondary),
                        borderColor: consumptionData.map(d => d.connection_type === 'Borne Fontaine' ? colors.primary + '80' : colors.secondary + '80'),
                        borderWidth: 1
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(html_template, height=700)

# Aliasing pour correspondre à app.py
render_leaflet_map = render_interactive_map
render_custom = render_interactive_dashboard
