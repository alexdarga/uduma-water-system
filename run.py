"""Script de démarrage pour le système Uduma Water Management"""

import subprocess
import sys
import time
import webbrowser
from threading import Thread
import os

def run_fastapi():
    """Démarrer l'API FastAPI"""
    print("🚀 Démarrage de l'API FastAPI...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage de FastAPI: {e}")
    except KeyboardInterrupt:
        print("\n🛑 API FastAPI arrêtée par l'utilisateur")

def run_streamlit():
    """Démarrer l'application Streamlit"""
    print("🎨 Démarrage de l'interface Streamlit...")
    time.sleep(3)  # Attendre que FastAPI soit prêt
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app/app.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage de Streamlit: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Interface Streamlit arrêtée par l'utilisateur")

def open_browser():
    """Ouvrir le navigateur après un délai"""
    time.sleep(8)  # Attendre que les services soient prêts
    print("🌐 Ouverture du navigateur...")
    try:
        webbrowser.open("http://localhost:8501")
    except Exception as e:
        print(f"⚠️ Impossible d'ouvrir le navigateur automatiquement: {e}")
        print("📋 Ouvrez manuellement: http://localhost:8501")

def check_dependencies():
    """Vérifier que les dépendances sont installées"""
    print("🔍 Vérification des dépendances...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'streamlit', 'sqlalchemy', 
        'pandas', 'plotly', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Packages manquants: {', '.join(missing_packages)}")
        print("💡 Exécutez: pip install -r requirements.txt")
        return False
    
    print("✅ Toutes les dépendances sont installées")
    return True

def check_database():
    """Vérifier que la base de données est initialisée"""
    print("🗄️ Vérification de la base de données...")
    
    if not os.path.exists("data/water_points.db"):
        print("⚠️ Base de données non trouvée")
        print("💡 Exécution de l'initialisation...")
        
        try:
            subprocess.run([sys.executable, "scripts/init_db.py"], check=True)
            subprocess.run([sys.executable, "scripts/data_import.py"], check=True)
            print("✅ Base de données initialisée avec succès")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    else:
        print("✅ Base de données trouvée")
    
    return True

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🌊 UDUMA WATER MANAGEMENT SYSTEM")
    print("=" * 60)
    
    # Vérifications préalables
    if not check_dependencies():
        sys.exit(1)
    
    if not check_database():
        sys.exit(1)
    
    print("\n🎯 Démarrage du système complet...")
    print("📝 Services:")
    print("   • API FastAPI: http://localhost:8000")
    print("   • Interface Streamlit: http://localhost:8501")
    print("   • Documentation API: http://localhost:8000/docs")
    
    try:
        # Créer les threads pour les deux services
        fastapi_thread = Thread(target=run_fastapi, daemon=True)
        streamlit_thread = Thread(target=run_streamlit, daemon=True)
        browser_thread = Thread(target=open_browser, daemon=True)
        
        # Démarrer les services
        fastapi_thread.start()
        streamlit_thread.start()
        browser_thread.start()
        
        print("\n✅ Système démarré avec succès!")
        print("🔄 Les services sont en cours d'exécution...")
        print("⚠️ Appuyez sur Ctrl+C pour arrêter")
        
        # Attendre que les threads se terminent
        while fastapi_thread.is_alive() or streamlit_thread.is_alive():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du système demandé par l'utilisateur")
        print("📋 Services arrêtés")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    finally:
        print("\n👋 Au revoir!")

if __name__ == "__main__":
    main()