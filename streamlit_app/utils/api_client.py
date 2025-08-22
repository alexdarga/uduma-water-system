"""Client API pour communiquer avec FastAPI depuis Streamlit"""

import requests
import streamlit as st
from typing import List, Dict, Optional
from datetime import date, datetime
import json

class UdumaAPIClient:
    """Client pour interagir avec l'API FastAPI"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def _handle_response(self, response: requests.Response) -> dict:
        """Gérer les réponses API et les erreurs"""
        try:
            response.raise_for_status()
            data = response.json()
            # Toujours renvoyer une liste ou dict uniforme
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data
            return {}
        except requests.exceptions.RequestException as e:
            st.error(f"Erreur API: {e}")
            return {} if 'kpis' in response.url else []
        except json.JSONDecodeError:
            st.error("Erreur de décodage JSON")
            return {} if 'kpis' in response.url else []
    
    def get_water_points(self, commune: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """Récupérer la liste des points d'eau"""
        params = {}
        if commune:
            params['commune'] = commune
        if status:
            params['status'] = status
        try:
            response = self.session.get(f"{self.base_url}/water_points", params=params)
            data = self._handle_response(response)
            return data if isinstance(data, list) else []
        except Exception as e:
            st.error(f"Erreur lors de la récupération des points d'eau: {e}")
            return []
    
    def get_consumption_stats(self, commune: Optional[str] = None, 
                              status: Optional[str] = None,
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None) -> List[Dict]:
        """Récupérer toutes les données de consommation avec filtres"""
        params = {}
        if commune: params['commune'] = commune
        if status: params['status'] = status
        if start_date:
            params['start_date'] = start_date.isoformat() if isinstance(start_date, date) else datetime.fromisoformat(start_date).date().isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat() if isinstance(end_date, date) else datetime.fromisoformat(end_date).date().isoformat()
        try:
            response = self.session.get(f"{self.base_url}/consumption", params=params)
            data = self._handle_response(response)
            # Toujours renvoyer une liste
            if isinstance(data, dict) and 'data' in data:
                return data['data']
            return data if isinstance(data, list) else []
        except Exception as e:
            st.error(f"Erreur lors de la récupération des données de consommation: {e}")
            return []
    
    def get_kpis(self) -> Dict:
        """Récupérer les KPIs du système"""
        try:
            response = self.session.get(f"{self.base_url}/analytics/kpis")
            data = self._handle_response(response)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            st.error(f"Erreur lors de la récupération des KPIs: {e}")
            return {}
    
    def get_anomalies(self) -> List[Dict]:
        """Récupérer les anomalies détectées"""
        try:
            response = self.session.get(f"{self.base_url}/analytics/anomalies")
            data = self._handle_response(response)
            return data if isinstance(data, list) else []
        except Exception as e:
            st.error(f"Erreur lors de la récupération des anomalies: {e}")
            return []
    
    def get_communes(self) -> List[str]:
        """Récupérer la liste des communes"""
        try:
            response = self.session.get(f"{self.base_url}/communes")
            data = self._handle_response(response)
            return data.get('communes', []) if isinstance(data, dict) else []
        except Exception as e:
            st.error(f"Erreur lors de la récupération des communes: {e}")
            return []
    
    def health_check(self) -> bool:
        """Vérifier si l'API est accessible"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def create_meter_reading(self, reading_data: Dict) -> Dict:
        """Créer un nouveau relevé de compteur"""
        try:
            response = self.session.post(f"{self.base_url}/meter_readings", json=reading_data)
            data = self._handle_response(response)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            st.error(f"Erreur lors de la création du relevé: {e}")
            return {}

# Instance globale du client API avec cache Streamlit
@st.cache_resource
def get_api_client() -> UdumaAPIClient:
    """Récupérer une instance unique et cachée du client API"""
    return UdumaAPIClient()