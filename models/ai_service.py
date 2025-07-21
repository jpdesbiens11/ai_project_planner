# models/ai_service.py
import requests
import json
import logging
import time
import re

class AIService:
    """Service pour interagir avec l'API d'IA."""
    
    def __init__(self, model_name, api_url):
        """Initialise le service avec le modèle et l'URL de l'API."""
        self.model = model_name
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)
        self.last_raw_response = ""  # Pour stocker la dernière réponse brute
    
    def generate_project_plan(self, project_description):
        """Génère un plan de projet à partir d'une description."""
        try:
            self.logger.info("Connexion à Ollama réussie")
            self.logger.info(f"Envoi d'une requête à {self.api_url}")
            
            prompt = f"""
Je veux créer un plan de projet pour un système de gestion de projet JIRA. Voici la description du projet:

{project_description}

Génère un plan détaillé comprenant:
1. Une structure EPIC/Story/Sous-tâche bien organisée
2. Les étapes principales du projet avec une estimation du temps
3. Une répartition logique des tâches
4. Les dépendances entre les tâches

Format ton plan de manière claire et structurée pour que je puisse facilement l'adapter à JIRA.
"""
            
            start_time = time.time()
            response = self._send_request(prompt)
            
            # Enregistrer la durée de la requête
            elapsed_time = time.time() - start_time
            self.logger.info(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du plan: {str(e)}")
            raise
    
    def generate_tasks_from_plan(self, plan_description):
        """Génère des tâches structurées à partir d'une description de plan."""
        try:
            self.logger.info("Connexion à Ollama réussie")
            self.logger.info(f"Envoi d'une requête à {self.api_url}")
            
            prompt = f"""
Tu dois transformer cette description de plan de projet en une liste de tâches JIRA structurées au format JSON.

Description du plan: {plan_description}

INSTRUCTIONS TRÈS IMPORTANTES:
1. Ta réponse doit être UNIQUEMENT un tableau JSON valide, sans texte d'introduction ou d'explication.
2. NE PAS inclure de délimiteurs markdown comme ```json ou ```.
3. Le format doit être EXACTEMENT comme ceci:
[
  {{
    "title": "Titre de la tâche 1",
    "description": "Description détaillée de la tâche",
    "status": "À faire",
    "priority": "Haute/Moyenne/Basse",
    "estimated_hours": 2,
    "assignee": "Non assigné",
    "type": "Epic/Story/Sous-tâche",
    "parent": null
  }},
  {{
    "title": "Titre de la tâche 2",
    "description": "Description détaillée de la tâche",
    "status": "À faire",
    "priority": "Haute/Moyenne/Basse",
    "estimated_hours": 1,
    "assignee": "Non assigné",
    "type": "Epic/Story/Sous-tâche",
    "parent": "Titre de la tâche parente ou null"
  }}
]

Crée au moins 10 tâches pertinentes pour ce projet. Pour les sous-tâches, assure-toi que la valeur "parent" correspond exactement au titre d'une tâche Epic ou Story.

IMPORTANT: Tu dois UNIQUEMENT renvoyer le tableau JSON, sans aucun texte ou explication autour. Le premier caractère doit être '[' et le dernier caractère doit être ']'.
"""

            start_time = time.time()
            response = self._send_request(prompt)
            
            # Enregistrer la durée de la requête
            elapsed_time = time.time() - start_time
            self.logger.info(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            # Nettoyer la réponse pour extraire uniquement le JSON
            json_str = self._extract_json(response)
            
            try:
                tasks = json.loads(json_str)
                return tasks
            except json.JSONDecodeError as e:
                self.logger.error(f"Erreur JSON: {str(e)}\nRéponse brute: {json_str[:200]}...")
                raise ValueError(f"Format JSON invalide ou non reconnu. Erreur: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération des tâches: {str(e)}")
            raise

    def analyze_tasks(self, tasks):
        """Analyse une liste de tâches et fournit des statistiques."""
        try:
            self.logger.info("Connexion à Ollama réussie")
            self.logger.info(f"Envoi d'une requête à {self.api_url}")
            
            # Préparer les données des tâches
            tasks_data = json.dumps(tasks, ensure_ascii=False, indent=2)
            
            prompt = f"""
Voici une liste de tâches de projet:

{tasks_data}

Fais une analyse complète de ces tâches et fournis:
1. Une vue d'ensemble du projet (objectifs, portée, structure)
2. La répartition des tâches par type (Epic, Story, Sous-tâche)
3. La répartition des tâches par priorité
4. Le temps total estimé pour le projet
5. Les tâches critiques qui pourraient être des goulots d'étranglement
6. Des suggestions pour améliorer la structure du projet

Format ta réponse de manière claire et structurée.
"""
            
            start_time = time.time()
            response = self._send_request(prompt)
            
            # Enregistrer la durée de la requête
            elapsed_time = time.time() - start_time
            self.logger.info(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des tâches: {str(e)}")
            raise
    
    def ask_question(self, question, tasks=None):
        """Répond à une question en se basant sur les tâches disponibles."""
        try:
            self.logger.info("Connexion à Ollama réussie")
            self.logger.info(f"Envoi d'une requête à {self.api_url}")
            
            # Préparer les données des tâches si disponibles
            tasks_context = ""
            if tasks:
                tasks_data = json.dumps(tasks, ensure_ascii=False, indent=2)
                tasks_context = f"""
En te basant sur ces tâches de projet:

{tasks_data}

"""
            
            prompt = f"""
{tasks_context}Réponds à cette question:

{question}

Donne une réponse claire, concise et informative.
"""
            
            start_time = time.time()
            response = self._send_request(prompt)
            
            # Enregistrer la durée de la requête
            elapsed_time = time.time() - start_time
            self.logger.info(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la réponse à la question: {str(e)}")
            raise
    
    def _send_request(self, prompt):
        """Envoie une requête à l'API Ollama."""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(self.api_url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            self.last_raw_response = response_text  # Stocker la réponse brute
            return response_text
        else:
            self.logger.error(f"Erreur {response.status_code}: {response.text}")
            raise Exception(f"Erreur lors de la connexion à Ollama: {response.status_code}")
    
    def _extract_json(self, text):
        """Extrait le JSON de la réponse du modèle, en supprimant les éventuels délimiteurs markdown."""
        # Essayons plusieurs méthodes pour extraire le JSON
        
        # 1. Chercher du JSON entre délimiteurs markdown
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, text)
        if matches:
            return matches[0].strip()
        
        # 2. Chercher du texte entre crochets