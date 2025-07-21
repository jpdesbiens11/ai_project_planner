# data/csv_manager.py
import csv
import os
import logging

class CSVManager:
    """Gère les opérations de lecture/écriture des tâches dans un fichier CSV."""
    
    # Définir les champs du CSV
    FIELDS = ['title', 'description', 'type', 'status', 'priority', 'estimated_hours', 'assignee', 'parent']
    
    def __init__(self, file_path):
        """Initialise le gestionnaire avec le chemin du fichier CSV."""
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        
        # Créer le fichier s'il n'existe pas
        if not os.path.exists(file_path):
            self._create_empty_file()
    
    def _create_empty_file(self):
        """Crée un fichier CSV vide avec les en-têtes."""
        try:
            directory = os.path.dirname(self.file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS)
                writer.writeheader()
                
            self.logger.info(f"Fichier CSV créé: {self.file_path}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du fichier CSV: {str(e)}")
            raise
    
    def read_tasks(self):
        """Lit toutes les tâches depuis le fichier CSV."""
        try:
            if not os.path.exists(self.file_path):
                self._create_empty_file()
                return []
            
            with open(self.file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                tasks = []
                
                for row in reader:
                    # Convertir la valeur d'estimated_hours en nombre si possible
                    if 'estimated_hours' in row:
                        try:
                            row['estimated_hours'] = float(row['estimated_hours'])
                        except (ValueError, TypeError):
                            # Garder la valeur telle quelle si elle n'est pas un nombre
                            pass
                    
                    # Gestion des valeurs null/None pour parent
                    if 'parent' in row and (row['parent'] == '' or row['parent'].lower() == 'null' or row['parent'].lower() == 'none'):
                        row['parent'] = None
                    
                    tasks.append(row)
                
                return tasks
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du fichier CSV: {str(e)}")
            raise
    
    def write_tasks(self, tasks):
        """Écrit toutes les tâches dans le fichier CSV."""
        try:
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS)
                writer.writeheader()
                writer.writerows(tasks)
                
            self.logger.info(f"{len(tasks)} tâches écrites dans {self.file_path}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'écriture dans le fichier CSV: {str(e)}")
            raise
    
    def add_task(self, task):
        """Ajoute une nouvelle tâche au fichier CSV."""
        try:
            tasks = self.read_tasks()
            tasks.append(task)
            self.write_tasks(tasks)
            
            self.logger.info(f"Tâche ajoutée: {task.get('title', 'Sans titre')}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            raise
    
    def update_task(self, index, task):
        """Met à jour une tâche existante."""
        try:
            tasks = self.read_tasks()
            
            if index < 0 or index >= len(tasks):
                raise ValueError(f"Index invalide: {index}")
            
            old_title = tasks[index].get('title')
            new_title = task.get('title')
            
            # Mettre à jour les références parent si le titre change
            if old_title != new_title:
                for i, t in enumerate(tasks):
                    if t.get('parent') == old_title:
                        tasks[i]['parent'] = new_title
            
            tasks[index] = task
            self.write_tasks(tasks)
            
            self.logger.info(f"Tâche mise à jour: {task.get('title', 'Sans titre')}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour de la tâche: {str(e)}")
            raise
    
    def delete_task(self, index):
        """Supprime une tâche existante."""
        try:
            tasks = self.read_tasks()
            
            if index < 0 or index >= len(tasks):
                raise ValueError(f"Index invalide: {index}")
            
            deleted_task = tasks.pop(index)
            self.write_tasks(tasks)
            
            self.logger.info(f"Tâche supprimée: {deleted_task.get('title', 'Sans titre')}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
            raise
            
    def add_tasks_from_json(self, tasks_data):
        """Ajoute des tâches à partir d'un objet JSON."""
        try:
            # Vérifier que tasks_data est une liste
            if not isinstance(tasks_data, list):
                raise ValueError("Les données des tâches doivent être une liste")
            
            # S'assurer que le fichier existe
            if not os.path.exists(self.file_path):
                # Créer le fichier avec les en-têtes
                with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.FIELDS)
                    writer.writeheader()
            
            # Lire les tâches existantes
            existing_tasks = self.read_tasks()
            
            # Ajouter les nouvelles tâches
            for task in tasks_data:
                # Valider et nettoyer les données
                task_dict = {}
                for field in self.FIELDS:
                    # Convertir camel_case en snake_case si nécessaire
                    camel_field = ''.join(x.capitalize() if i > 0 else x for i, x in enumerate(field.split('_')))
                    
                    # Essayer différentes variations du nom de champ
                    if field in task:
                        task_dict[field] = task[field]
                    elif camel_field in task:
                        task_dict[field] = task[camel_field]
                    elif field.lower() in task:
                        task_dict[field] = task[field.lower()]
                    else:
                        # Champ manquant, utiliser une valeur par défaut
                        if field == 'status':
                            task_dict[field] = 'À faire'
                        elif field == 'priority':
                            task_dict[field] = 'Moyenne'
                        elif field == 'estimated_hours':
                            task_dict[field] = 0
                        elif field == 'assignee':
                            task_dict[field] = 'Non assigné'
                        else:
                            task_dict[field] = ''
                
                # Ajouter la tâche
                existing_tasks.append(task_dict)
            
            # Écrire toutes les tâches dans le fichier
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS)
                writer.writeheader()
                writer.writerows(existing_tasks)
            
            return len(tasks_data)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout des tâches depuis JSON: {str(e)}")
            raise