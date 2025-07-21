import requests
import json
import logging
import time
import re
import io
import subprocess

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
            
            # Prompt modifié pour améliorer la génération de JSON valide
            prompt = f"""
Tu dois transformer cette description de plan de projet en une liste de tâches JIRA structurées au format JSON.

Description du plan: {plan_description}

INSTRUCTIONS TRÈS IMPORTANTES:
1. Ta réponse doit être UNIQUEMENT un tableau JSON valide, sans texte d'introduction ou d'explication.
2. NE PAS inclure de délimiteurs markdown comme ```json ou ```.
3. CHAQUE tâche doit être SIMPLE et CONCISE.
4. LIMITE-TOI à 5 TÂCHES MAXIMUM pour garantir une réponse complète.
5. Le premier caractère doit être '[' et le dernier caractère doit être ']'.

Le format doit être EXACTEMENT comme ceci:
[
  {{
    "title": "TITRE COURT DE LA TÂCHE 1",
    "description": "DESCRIPTION COURTE",
    "status": "À faire",
    "priority": "Haute",
    "estimated_hours": 2,
    "assignee": null,
    "type": "Epic",
    "parent": null
  }},
  {{
    "title": "TITRE COURT DE LA SOUS-TÂCHE",
    "description": "DESCRIPTION COURTE",
    "status": "À faire",
    "priority": "Moyenne",
    "estimated_hours": 1,
    "assignee": null,
    "type": "Sous-tâche",
    "parent": "TITRE COURT DE LA TÂCHE 1"
  }}
]

RÉPONDS UNIQUEMENT AVEC LE TABLEAU JSON. Aucun texte avant ou après.
"""
            
            start_time = time.time()
            response = self._send_request(prompt)
            
            # Enregistrer la durée de la requête
            elapsed_time = time.time() - start_time
            self.logger.info(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            # Stocker la réponse complète
            self.last_raw_response = response
            
            # Nettoyer la réponse pour extraire uniquement le JSON
            json_str = self._extract_json(response)
            
            if not json_str:
                self.logger.error("Aucun JSON valide n'a été trouvé dans la réponse")
                self.logger.debug(f"Réponse brute: {response[:200]}...")
                
                # Faire une seconde tentative avec un prompt plus simple
                self.logger.info("Tentative de récupération avec un prompt plus simple...")
                
                simple_prompt = f"""
Analyse cette description de plan de projet:
{plan_description}

Crée exactement 3 tâches JIRA au format JSON, comme ceci:
[
  {{
    "title": "TITRE COURT",
    "description": "DESCRIPTION COURTE",
    "status": "À faire",
    "priority": "Haute",
    "estimated_hours": 2,
    "type": "Epic"
  }},
  {{
    "title": "TITRE COURT 2",
    "description": "DESCRIPTION COURTE",
    "status": "À faire", 
    "priority": "Moyenne",
    "estimated_hours": 1,
    "type": "Story"
  }},
  {{
    "title": "TITRE COURT 3",
    "description": "DESCRIPTION COURTE",
    "status": "À faire",
    "priority": "Basse",
    "estimated_hours": 0.5,
    "type": "Sous-tâche"
  }}
]

RÉPONDS UNIQUEMENT AVEC LE TABLEAU JSON. Pas de texte avant ou après.
"""
                
                retry_response = self._send_request(simple_prompt)
                self.last_raw_response = retry_response
                json_str = self._extract_json(retry_response)
                
                if not json_str:
                    # Si toujours pas de JSON, créer manuellement 3 tâches simples
                    self.logger.warning("Création manuelle de tâches simples basées sur le plan")
                    
                    # Extraire quelques éléments du plan
                    lines = plan_description.split('\n')
                    potential_titles = [line for line in lines if len(line.strip()) > 10 and len(line.strip()) < 50]
                    
                    titles = []
                    for i in range(min(3, len(potential_titles))):
                        titles.append(potential_titles[i].strip())
                    
                    # Ajouter des titres par défaut si nécessaire
                    while len(titles) < 3:
                        titles.append(f"Tâche {len(titles) + 1} du projet")
                    
                    # Créer un JSON simple
                    tasks = [
                        {
                            "title": titles[0],
                            "description": "Tâche principale du projet",
                            "status": "À faire",
                            "priority": "Haute",
                            "estimated_hours": 8,
                            "assignee": None,
                            "type": "Epic",
                            "parent": None
                        },
                        {
                            "title": titles[1],
                            "description": "Story du projet",
                            "status": "À faire",
                            "priority": "Moyenne",
                            "estimated_hours": 4,
                            "assignee": None,
                            "type": "Story",
                            "parent": None
                        },
                        {
                            "title": titles[2],
                            "description": "Sous-tâche du projet",
                            "status": "À faire",
                            "priority": "Normale",
                            "estimated_hours": 2,
                            "assignee": None,
                            "type": "Sous-tâche",
                            "parent": titles[1]
                        }
                    ]
                    
                    return tasks
            
            try:
                tasks = json.loads(json_str)
                return tasks
            except json.JSONDecodeError as e:
                self.logger.error(f"Erreur JSON: {str(e)}\nRéponse brute: {json_str[:200]}...")
                
                # Tentative de réparation du JSON
                repaired_json = self._repair_json(json_str)
                if repaired_json:
                    return repaired_json
                    
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
    
    def ask_question_with_csv(self, prompt, csv_path):
        """Use Ollama CLI to ask a question with CSV file reference"""
        try:
            # Create a more detailed prompt
            full_prompt = f"""
J'ai un fichier CSV situé à: {csv_path}
Ce fichier contient des données que je dois analyser.

Question de l'utilisateur: {prompt}

Analyse le fichier CSV et réponds à la question de manière détaillée.
"""
            
            # Construct a command to run Ollama CLI
            cmd = ["ollama", "run", self.model, full_prompt]
            
            # Run the command
            self.logger.info(f"Exécution d'Ollama CLI avec le modèle {self.model}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Get the output
            if result.returncode == 0:
                self.logger.info("Réponse reçue avec succès d'Ollama CLI")
                return result.stdout
            else:
                error_msg = f"Erreur lors de l'exécution d'Ollama CLI: {result.stderr}"
                self.logger.error(error_msg)
                return f"Erreur: {error_msg}"
        except Exception as e:
            self.logger.error(f"Exception lors de l'exécution d'Ollama CLI: {str(e)}")
            return f"Erreur: {str(e)}"
    
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
        """Extrait le JSON de la réponse du modèle, avec des méthodes multiples pour plus de robustesse."""
        if not text:
            return None
            
        # Méthode 1: Chercher du JSON entre délimiteurs markdown
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, text)
        if matches:
            return matches[0].strip()
        
        # Méthode 2: Chercher un tableau JSON complet
        array_pattern = r"\[\s*\{[\s\S]*\}\s*\]"
        matches = re.search(array_pattern, text)
        if matches:
            return matches.group(0).strip()
            
        # Méthode 3: Chercher le début et la fin d'un tableau JSON
        if text.strip().startswith('[') and text.strip().endswith(']'):
            # Vérifier s'il contient au moins un objet JSON
            if '{' in text and '}' in text:
                return text.strip()
        
        # Méthode 4: Chercher plusieurs objets JSON
        objects_pattern = r"\{\s*\"[^\"]+\"\s*:[\s\S]*?\}"
        matches = re.findall(objects_pattern, text)
        if matches and len(matches) > 0:
            # Tenter de construire un tableau à partir des objets trouvés
            return "[" + ",".join(matches) + "]"
        
        # Aucun JSON trouvé
        return None
    
    def _repair_json(self, json_str):
        """Tente de réparer un JSON invalide."""
        try:
            # Vérifier si le problème est des virgules finales
            fixed_str = re.sub(r',\s*}', '}', json_str)
            fixed_str = re.sub(r',\s*]', ']', fixed_str)
            
            # Tenter de charger le JSON réparé
            try:
                return json.loads(fixed_str)
            except:
                pass
            
            # Extraire des objets individuels
            objects_pattern = r"\{\s*\"[^\"]+\"\s*:[\s\S]*?\}"
            matches = re.findall(objects_pattern, json_str)
            
            if matches and len(matches) > 0:
                valid_objects = []
                for obj_str in matches:
                    try:
                        # Réparer les virgules finales
                        obj_str = re.sub(r',\s*}', '}', obj_str)
                        # Tester si l'objet est valide
                        json.loads(obj_str)
                        valid_objects.append(obj_str)
                    except:
                        pass
                
                if valid_objects:
                    return json.loads("[" + ",".join(valid_objects) + "]")
            
            # Si nous arrivons ici, nous n'avons pas pu réparer le JSON
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la réparation du JSON: {str(e)}")
            return None