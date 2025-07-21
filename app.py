# app.py
import os
import sys
import argparse
import logging
import requests
import json
import time
from typing import List, Dict, Tuple, Set, Optional

# Ajouter le répertoire du projet au chemin d'importation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.ai_service import AIService
from data.csv_manager import CSVManager
from ui.cli_interface import CLIInterface

def setup_logging():
    """Configure le système de journalisation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
        ]
    )
    return logging.getLogger(__name__)

def get_available_models(api_base_url: str) -> List[Dict]:
    """Récupère la liste des modèles déjà téléchargés depuis l'API Ollama."""
    try:
        # Extraire le domaine et le port de l'API generate
        parts = api_base_url.split('/api/')
        if len(parts) < 2:
            return []
        base_url = f"{parts[0]}/api/tags"
        
        response = requests.get(base_url)
        if response.status_code == 200:
            return response.json().get('models', [])
        return []
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des modèles: {str(e)}")
        return []

def download_model(api_base_url: str, model_name: str) -> bool:
    """Télécharge un modèle depuis Ollama."""
    try:
        # Extraire le domaine et le port de l'API generate
        parts = api_base_url.split('/api/')
        if len(parts) < 2:
            return False
        base_url = f"{parts[0]}/api/pull"
        
        print(f"\nTéléchargement du modèle {model_name}...")
        print("Ce processus peut prendre plusieurs minutes selon votre connexion internet.")
        print("Veuillez patienter...")
        
        response = requests.post(
            base_url,
            json={"name": model_name},
            stream=True  # Pour suivre le téléchargement
        )
        
        # Suivi du téléchargement
        if response.status_code == 200:
            total_received = 0
            status_printed = False
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        if not status_printed or data.get('completed', False):
                            print(f"Status: {data['status']}")
                            status_printed = True
                    if 'total' in data and 'completed' in data:
                        total = data['total']
                        completed = data['completed']
                        if total > 0:
                            percent = int((completed / total) * 100)
                            print(f"Progression: {percent}% ({completed}/{total})", end='\r')
                    total_received += len(line)
            
            print("\nTéléchargement terminé avec succès!")
            return True
        else:
            print(f"Échec du téléchargement: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Erreur lors du téléchargement du modèle: {str(e)}")
        return False

def get_model_specs() -> Dict[str, Dict]:
    """Définit les spécifications des modèles recommandés."""
    return {
        # Llama 3.2 models
        "llama3.2:1b": {
            "size": "1B",
            "ram": "2-4 GB",
            "gpu": "Optionnel",
            "description": "Très petit modèle de chat général. Performant pour du texte simple."
        },
        "llama3.2:3b": {
            "size": "3B",
            "ram": "4-6 GB",
            "gpu": "Optionnel",
            "description": "Petit modèle de chat équilibré. Bon compromis performance/ressources."
        },
        
        # Qwen2.5 models
        "qwen2.5:0.5b": {
            "size": "0.5B",
            "ram": "1-2 GB",
            "gpu": "Non requis",
            "description": "Modèle ultra-léger, idéal pour les systèmes très limités."
        },
        "qwen2.5:1.5b": {
            "size": "1.5B",
            "ram": "2-4 GB",
            "gpu": "Non requis",
            "description": "Modèle très léger avec bonnes performances générales."
        },
        "qwen2.5:3b": {
            "size": "3B",
            "ram": "4-6 GB",
            "gpu": "Optionnel",
            "description": "Modèle compact avec bonnes capacités multilingues."
        },
        "qwen2.5:7b": {
            "size": "7B",
            "ram": "8-12 GB",
            "gpu": "Recommandé",
            "description": "Modèle puissant, multilingue, avec bonnes capacités de raisonnement."
        },
        
        # Qwen2.5-coder models
        "qwen2.5-coder:0.5b": {
            "size": "0.5B",
            "ram": "1-2 GB",
            "gpu": "Non requis",
            "description": "Modèle ultra-léger optimisé pour le code simple."
        },
        "qwen2.5-coder:1.5b": {
            "size": "1.5B",
            "ram": "2-4 GB",
            "gpu": "Non requis",
            "description": "Modèle léger optimisé pour la programmation."
        },
        "qwen2.5-coder:3b": {
            "size": "3B",
            "ram": "4-6 GB",
            "gpu": "Optionnel",
            "description": "Modèle compact avec de bonnes capacités de codage et traitement de données."
        },
        "qwen2.5-coder:7b": {
            "size": "7B",
            "ram": "8-12 GB",
            "gpu": "Recommandé",
            "description": "Modèle performant pour le développement et la documentation."
        },
        
        # Gemma models
        "gemma:2b": {
            "size": "2B",
            "ram": "4 GB",
            "gpu": "Non requis",
            "description": "Modèle compact de Google, bon pour les tâches générales."
        },
        "gemma:7b": {
            "size": "7B",
            "ram": "8-12 GB",
            "gpu": "Recommandé",
            "description": "Modèle puissant de Google, polyvalent."
        },
        
        # Gemma3n models
        "gemma3n:e2b": {
            "size": "2B (efficace)",
            "ram": "3-4 GB",
            "gpu": "Non requis",
            "description": "Modèle optimisé pour appareils de faible puissance."
        },
        "gemma3n:e4b": {
            "size": "4B (efficace)",
            "ram": "5-6 GB",
            "gpu": "Optionnel",
            "description": "Version plus puissante, optimisée pour laptops standard."
        },
        
        # Phi models
        "phi3:3.8b": {
            "size": "3.8B",
            "ram": "4-6 GB",
            "gpu": "Optionnel",
            "description": "Modèle compact de Microsoft avec bonnes performances de raisonnement et traitement de données."
        },
        "phi4:14b": {
            "size": "14B",
            "ram": "16+ GB",
            "gpu": "Recommandé",
            "description": "Modèle puissant de Microsoft, peut nécessiter plus de ressources."
        },
        "phi4-mini:3.8b": {
            "size": "3.8B",
            "ram": "4-6 GB",
            "gpu": "Optionnel",
            "description": "Version légère de Phi4, optimisée pour usage sur laptop."
        },
        
        # Small models
        "tinyllama:1.1b": {
            "size": "1.1B",
            "ram": "2 GB",
            "gpu": "Non requis",
            "description": "Version extrêmement compacte de Llama, très rapide."
        },
        "smollm:135m": {
            "size": "135M",
            "ram": "512 MB",
            "gpu": "Non requis",
            "description": "Ultra-petit modèle, performances limitées mais très économe."
        },
        "smollm:360m": {
            "size": "360M",
            "ram": "1 GB",
            "gpu": "Non requis",
            "description": "Très petit modèle avec performances modestes."
        },
        "smollm:1.7b": {
            "size": "1.7B",
            "ram": "2-3 GB",
            "gpu": "Non requis",
            "description": "Petit modèle avec bon équilibre taille/performances."
        },
        "smollm2:135m": {
            "size": "135M",
            "ram": "512 MB",
            "gpu": "Non requis",
            "description": "Version améliorée de SmolLM, ultra-compact."
        },
        "smollm2:360m": {
            "size": "360M",
            "ram": "1 GB",
            "gpu": "Non requis",
            "description": "Version améliorée, très petit modèle."
        },
        "smollm2:1.7b": {
            "size": "1.7B",
            "ram": "2-3 GB",
            "gpu": "Non requis",
            "description": "Version améliorée, petit modèle équilibré."
        },
        
        # Other useful models
        "moondream:1.8b": {
            "size": "1.8B",
            "ram": "3 GB",
            "gpu": "Non requis",
            "description": "Petit modèle multimodal (texte+image) léger."
        },
        "stable-code:3b": {
            "size": "3B",
            "ram": "4-6 GB",
            "gpu": "Optionnel",
            "description": "Modèle spécialisé pour la génération de code, compact."
        },
        "mistral:7b": {
            "size": "7B",
            "ram": "8-12 GB",
            "gpu": "Recommandé",
            "description": "Modèle puissant avec bonnes performances de raisonnement."
        },
        "neural-chat:7b": {
            "size": "7B",
            "ram": "8-12 GB",
            "gpu": "Recommandé",
            "description": "Modèle conversationnel basé sur Mistral, polyvalent."
        },
        "stablelm2:1.6b": {
            "size": "1.6B",
            "ram": "2-3 GB",
            "gpu": "Non requis",
            "description": "Modèle compact multilingue, adapté aux laptops."
        }
    }

def select_model(api_url: str, default_model: str) -> str:
    """Affiche un menu pour sélectionner un modèle d'IA et retourne le choix."""
    # Récupérer les modèles déjà installés
    installed_models = get_available_models(api_url)
    installed_model_names = set()
    
    for model in installed_models:
        model_name = model['name']
        tag = model.get('tag', 'default')
        if tag != 'default':
            installed_model_names.add(f"{model_name}:{tag}")
        else:
            installed_model_names.add(model_name)
    
    # Obtenir les spécifications de tous les modèles recommandés
    all_model_specs = get_model_specs()
    
    print("\n===== SÉLECTION DU MODÈLE D'IA =====")
    print("Modèles recommandés pour votre P52:")
    
    # Grouper les modèles par famille
    model_families = {}
    for model_name, specs in all_model_specs.items():
        family = model_name.split(':')[0]
        if family not in model_families:
            model_families[family] = []
        model_families[family].append((model_name, specs))
    
    # Afficher les modèles par famille, triés par taille
    display_models = []
    for family, models in sorted(model_families.items()):
        print(f"\n-- Famille {family.upper()} --")
        for i, (model_name, specs) in enumerate(sorted(models, key=lambda x: float(x[1]['size'].replace('B', '').replace('M', 'e-3').replace('K', 'e-6').replace(' ', '').replace('(efficace)', '')), reverse=False)):
            size = specs['size']
            ram = specs['ram']
            gpu = specs['gpu']
            description = specs['description']
            
            # Marquer comme installé ou non
            status = "✓ INSTALLÉ" if model_name in installed_model_names else "○ Non installé"
            display_index = len(display_models) + 1
            display_models.append(model_name)
            
            print(f"{display_index}. {model_name} [{status}]")
            print(f"   Taille: {size} | RAM: {ram} | GPU: {gpu}")
            print(f"   {description}")
    
    # Ajouter option pour saisie manuelle
    print(f"\n{len(display_models) + 1}. Autre modèle (saisie manuelle)")
    
    # Demander à l'utilisateur de faire un choix
    while True:
        try:
            choice = input("\nEntrez le numéro du modèle à utiliser: ")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(display_models):
                selected_model = display_models[choice_num - 1]
                
                # Vérifier si le modèle est déjà installé
                if selected_model not in installed_model_names:
                    print(f"\nLe modèle {selected_model} n'est pas encore installé.")
                    download = input("Voulez-vous le télécharger maintenant? (o/n): ").lower()
                    if download == 'o' or download == 'oui':
                        success = download_model(api_url, selected_model)
                        if not success:
                            print("Échec du téléchargement. Veuillez essayer un autre modèle.")
                            continue
                    else:
                        print("Téléchargement annulé. Veuillez choisir un autre modèle.")
                        continue
                
                return selected_model
                
            elif choice_num == len(display_models) + 1:
                manual_model = input("Entrez le nom du modèle (format: nom:tag): ")
                
                # Vérifier si le modèle saisi manuellement est déjà installé
                if manual_model not in installed_model_names:
                    print(f"\nLe modèle {manual_model} n'est pas encore installé.")
                    download = input("Voulez-vous le télécharger maintenant? (o/n): ").lower()
                    if download == 'o' or download == 'oui':
                        success = download_model(api_url, manual_model)
                        if not success:
                            print("Échec du téléchargement. Veuillez essayer un autre modèle.")
                            continue
                    else:
                        print("Téléchargement annulé. Veuillez choisir un autre modèle.")
                        continue
                
                return manual_model
            else:
                print("Choix invalide. Veuillez réessayer.")
        except ValueError:
            print("Veuillez entrer un nombre.")

def main():
    """Point d'entrée principal de l'application."""
    logger = setup_logging()
    logger.info("Démarrage de l'application")
    
    # Analyser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Agent de planification de projet JIRA avec IA")
    parser.add_argument("--file", "-f", default="jira_tasks.csv", help="Chemin vers le fichier CSV des tâches")
    parser.add_argument("--model", "-m", default="llama3.2:3b",
                       help="Nom du modèle d'IA à utiliser (ex: llama3.2:3b, qwen2.5-coder:7b)")
    parser.add_argument("--api", "-a", default="http://localhost:11434/api/generate",
                       help="URL de l'API Ollama")
    parser.add_argument("--verbose", "-v", action="store_true", help="Active les logs détaillés")
    parser.add_argument("--skip-model-selection", "-s", action="store_true", 
                        help="Sauter la sélection du modèle et utiliser directement celui spécifié en argument")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Créer les répertoires nécessaires
    app_dir = os.path.dirname(os.path.abspath(__file__))
    for directory in ["data", "models", "ui"]:
        os.makedirs(os.path.join(app_dir, directory), exist_ok=True)
    
    # Sélection du modèle si non désactivée
    model_name = args.model
    if not args.skip_model_selection:
        model_name = select_model(args.api, args.model)
        logger.info(f"Modèle sélectionné par l'utilisateur: {model_name}")
    else:
        # Vérifier si le modèle spécifié est installé
        installed_models = get_available_models(args.api)
        installed_model_names = set()
        for model in installed_models:
            model_name_with_tag = f"{model['name']}:{model.get('tag', 'default')}" if model.get('tag', 'default') != 'default' else model['name']
            installed_model_names.add(model_name_with_tag)
        
        if model_name not in installed_model_names:
            print(f"\nLe modèle {model_name} n'est pas encore installé.")
            download = input("Voulez-vous le télécharger maintenant? (o/n): ").lower()
            if download == 'o' or download == 'oui':
                success = download_model(args.api, model_name)
                if not success:
                    print(f"Échec du téléchargement du modèle {model_name}. L'application va s'arrêter.")
                    sys.exit(1)
            else:
                print("Téléchargement annulé. L'application va s'arrêter.")
                sys.exit(1)
    
    # Initialiser les services
    try:
        # Utiliser un chemin absolu pour le fichier CSV
        file_path = args.file
        if not os.path.isabs(file_path):
            file_path = os.path.join(app_dir, file_path)
        
        logger.info(f"Utilisation du fichier CSV: {file_path}")
        logger.info(f"Modèle d'IA utilisé: {model_name}")
        
        csv_manager = CSVManager(file_path)
        ai_service = AIService(model_name, args.api)
        cli_interface = CLIInterface(ai_service, csv_manager)
        
        # Exécuter l'interface
        cli_interface.run()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()