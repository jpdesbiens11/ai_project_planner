# ui/cli_interface.py
import os
import time

class CLIInterface:
    """Interface en ligne de commande pour l'application."""
    
    def __init__(self, ai_service, csv_manager):
        """Initialise l'interface avec les services requis."""
        self.ai_service = ai_service
        self.csv_manager = csv_manager
    
    def run(self):
        """Exécute la boucle principale de l'interface."""
        self.print_header()
        
        while True:
            try:
                command = input("> ")
                if not command:
                    continue
                
                parts = command.strip().split(" ", 1)
                cmd = parts[0].lower()
                args = parts[1].strip() if len(parts) > 1 else ""
                
                if cmd == "exit":
                    print("Au revoir!")
                    break
                elif cmd == "help":
                    self.print_help()
                elif cmd == "list":
                    self.handle_list_command()
                elif cmd == "view":
                    self.handle_view_command(args)
                elif cmd == "add":
                    self.handle_add_command()
                elif cmd == "edit":
                    self.handle_edit_command(args)
                elif cmd == "delete":
                    self.handle_delete_command(args)
                elif cmd == "search":
                    self.handle_search_command(args)
                elif cmd == "ask":
                    self.handle_ask_command(args)
                elif cmd == "plan":
                    self.handle_plan_command(args)
                elif cmd == "export":
                    self.handle_export_command(args)
                else:
                    print(f"Commande '{cmd}' inconnue. Tapez 'help' pour voir les commandes disponibles.")
            except Exception as e:
                print(f"Erreur: {str(e)}")
    
    def print_header(self):
        """Affiche l'en-tête de l'application."""
        print("=" * 80)
        print("AGENT DE PLANIFICATION JIRA".center(80))
        print("=" * 80)
        
        # Afficher les informations sur le fichier
        file_path = self.csv_manager.file_path
        tasks = self.csv_manager.read_tasks()
        
        print(f"Fichier: {file_path}")
        print(f"Nombre de tâches: {len(tasks)}")
        print("-" * 80)
        
        self.print_help()
    
    def print_help(self):
        """Affiche l'aide des commandes disponibles."""
        commands = [
            ("list", "Affiche toutes les tâches"),
            ("view <index>", "Affiche les détails d'une tâche"),
            ("add", "Ajoute une nouvelle tâche"),
            ("edit <index>", "Modifie une tâche existante"),
            ("delete <index>", "Supprime une tâche"),
            ("search <texte>", "Recherche des tâches"),
            ("ask <question>", "Pose une question à l'IA"),
            ("plan <description>", "Demande à l'IA de générer un plan"),
            ("export <fichier>", "Exporte les tâches vers un autre fichier"),
            ("help", "Affiche cette aide"),
            ("exit", "Quitte l'application")
        ]
        
        print("Commandes disponibles:")
        for cmd, desc in commands:
            print(f"  {cmd:<22} - {desc}")
    
    def handle_list_command(self):
        """Affiche la liste des tâches."""
        tasks = self.csv_manager.read_tasks()
        
        if not tasks:
            print("Aucune tâche trouvée.")
            return
        
        print("\nListe des tâches:")
        print("-" * 80)
        print(f"{'ID':<5} {'Titre':<40} {'Type':<15} {'Statut':<10} {'Priorité':<10}")
        print("-" * 80)
        
        for i, task in enumerate(tasks, 1):
            title = task.get('title', 'Sans titre')
            task_type = task.get('type', 'N/A')
            status = task.get('status', 'N/A')
            priority = task.get('priority', 'N/A')
            
            # Tronquer le titre s'il est trop long
            if len(title) > 37:
                title = title[:34] + "..."
            
            print(f"{i:<5} {title:<40} {task_type:<15} {status:<10} {priority:<10}")
    
    def handle_view_command(self, args):
        """Affiche les détails d'une tâche spécifique."""
        if not args:
            print("Veuillez spécifier l'index de la tâche à afficher.")
            return
        
        try:
            index = int(args) - 1
            tasks = self.csv_manager.read_tasks()
            
            if index < 0 or index >= len(tasks):
                print(f"Index invalide. Il y a {len(tasks)} tâches.")
                return
            
            task = tasks[index]
            
            print("\nDétails de la tâche:")
            print("-" * 80)
            print(f"Titre: {task.get('title', 'N/A')}")
            print(f"Description: {task.get('description', 'N/A')}")
            print(f"Type: {task.get('type', 'N/A')}")
            print(f"Statut: {task.get('status', 'N/A')}")
            print(f"Priorité: {task.get('priority', 'N/A')}")
            print(f"Estimation (heures): {task.get('estimated_hours', 'N/A')}")
            print(f"Assigné à: {task.get('assignee', 'Non assigné')}")
            
            parent = task.get('parent', None)
            if parent:
                print(f"Parent: {parent}")
            
            # Trouver les sous-tâches
            subtasks = []
            for i, t in enumerate(tasks):
                if t.get('parent') == task.get('title'):
                    subtasks.append((i + 1, t.get('title')))
            
            if subtasks:
                print("\nSous-tâches:")
                for idx, title in subtasks:
                    print(f"  {idx}. {title}")
            
        except ValueError:
            print("L'index doit être un nombre.")
    
    def handle_add_command(self):
        """Ajoute une nouvelle tâche."""
        print("\nAjouter une nouvelle tâche:")
        
        # Obtenir les entrées de l'utilisateur
        title = input("Titre: ")
        description = input("Description: ")
        
        # Type de tâche
        print("\nTypes disponibles: Epic, Story, Sous-tâche")
        task_type = input("Type [Story]: ") or "Story"
        
        # Parent (pour les sous-tâches)
        parent = None
        if task_type.lower() == "sous-tâche":
            tasks = self.csv_manager.read_tasks()
            
            # Afficher les tâches potentiellement parentes
            print("\nTâches disponibles comme parent:")
            parents = []
            for i, task in enumerate(tasks):
                if task.get('type', '').lower() in ['epic', 'story']:
                    print(f"{i+1}. {task.get('title')}")
                    parents.append(task)
            
            if parents:
                parent_idx = input("\nIndex du parent (laissez vide pour aucun): ")
                if parent_idx:
                    try:
                        parent_idx = int(parent_idx) - 1
                        if 0 <= parent_idx < len(parents):
                            parent = parents[parent_idx].get('title')
                    except ValueError:
                        print("Index invalide, aucun parent ne sera défini.")
            else:
                print("Aucune tâche Epic ou Story disponible comme parent.")
        
        # Autres informations
        status = input("Statut [À faire]: ") or "À faire"
        priority = input("Priorité (Haute/Moyenne/Basse) [Moyenne]: ") or "Moyenne"
        
        estimated_hours = input("Estimation en heures [1]: ") or "1"
        try:
            estimated_hours = float(estimated_hours)
        except ValueError:
            print("Valeur d'estimation invalide, utilisation de la valeur par défaut: 1")
            estimated_hours = 1
        
        assignee = input("Assigné à [Non assigné]: ") or "Non assigné"
        
        # Créer la nouvelle tâche
        new_task = {
            'title': title,
            'description': description,
            'type': task_type,
            'status': status,
            'priority': priority,
            'estimated_hours': estimated_hours,
            'assignee': assignee,
            'parent': parent
        }
        
        # Ajouter la tâche
        self.csv_manager.add_task(new_task)
        print("Tâche ajoutée avec succès!")
    
    def handle_edit_command(self, args):
        """Modifie une tâche existante."""
        if not args:
            print("Veuillez spécifier l'index de la tâche à modifier.")
            return
        
        try:
            index = int(args) - 1
            tasks = self.csv_manager.read_tasks()
            
            if index < 0 or index >= len(tasks):
                print(f"Index invalide. Il y a {len(tasks)} tâches.")
                return
            
            task = tasks[index]
            print(f"\nModification de la tâche: {task.get('title')}")
            
            # Obtenir les nouvelles valeurs (ou garder les anciennes)
            title = input(f"Titre [{task.get('title', '')}]: ") or task.get('title', '')
            description = input(f"Description [{task.get('description', '')}]: ") or task.get('description', '')
            task_type = input(f"Type [{task.get('type', '')}]: ") or task.get('type', '')
            status = input(f"Statut [{task.get('status', '')}]: ") or task.get('status', '')
            priority = input(f"Priorité [{task.get('priority', '')}]: ") or task.get('priority', '')
            
            estimated_hours = input(f"Estimation en heures [{task.get('estimated_hours', '')}]: ") or task.get('estimated_hours', '')
            try:
                estimated_hours = float(estimated_hours)
            except ValueError:
                print(f"Valeur d'estimation invalide, utilisation de la valeur précédente: {task.get('estimated_hours', 1)}")
                estimated_hours = task.get('estimated_hours', 1)
            
            assignee = input(f"Assigné à [{task.get('assignee', '')}]: ") or task.get('assignee', '')
            
            # Parent (pour les sous-tâches)
            current_parent = task.get('parent', None)
            if task_type.lower() == "sous-tâche":
                parent_prompt = f"Parent [{current_parent if current_parent else 'Aucun'}]: "
                new_parent = input(parent_prompt)
                if new_parent:
                    parent = new_parent
                else:
                    parent = current_parent
            else:
                parent = None
            
            # Mettre à jour la tâche
            updated_task = {
                'title': title,
                'description': description,
                'type': task_type,
                'status': status,
                'priority': priority,
                'estimated_hours': estimated_hours,
                'assignee': assignee,
                'parent': parent
            }
            
            # Mettre à jour les parents des sous-tâches si le titre a changé
            if title != task.get('title'):
                for i, t in enumerate(tasks):
                    if t.get('parent') == task.get('title'):
                        t['parent'] = title
                        tasks[i] = t
            
            tasks[index] = updated_task
            self.csv_manager.write_tasks(tasks)
            print("Tâche modifiée avec succès!")
            
        except ValueError:
            print("L'index doit être un nombre.")
    
    def handle_delete_command(self, args):
        """Supprime une tâche."""
        if not args:
            print("Veuillez spécifier l'index de la tâche à supprimer.")
            return
        
        try:
            index = int(args) - 1
            tasks = self.csv_manager.read_tasks()
            
            if index < 0 or index >= len(tasks):
                print(f"Index invalide. Il y a {len(tasks)} tâches.")
                return
            
            task = tasks[index]
            
            # Vérifier s'il y a des sous-tâches
            has_subtasks = False
            for t in tasks:
                if t.get('parent') == task.get('title'):
                    has_subtasks = True
                    break
            
            if has_subtasks:
                confirm = input("Cette tâche a des sous-tâches. Voulez-vous vraiment la supprimer? (o/n): ")
                if confirm.lower() != 'o' and confirm.lower() != 'oui':
                    print("Suppression annulée.")
                    return
            
            # Supprimer la tâche
            tasks.pop(index)
            self.csv_manager.write_tasks(tasks)
            print("Tâche supprimée avec succès!")
            
        except ValueError:
            print("L'index doit être un nombre.")
    
    def handle_search_command(self, args):
        """Recherche des tâches par texte."""
        if not args:
            print("Veuillez spécifier un texte à rechercher.")
            return
        
        search_text = args.lower()
        tasks = self.csv_manager.read_tasks()
        
        # Filtrer les tâches
        results = []
        for i, task in enumerate(tasks):
            # Rechercher dans le titre et la description
            title = task.get('title', '').lower()
            description = task.get('description', '').lower()
            
            if search_text in title or search_text in description:
                results.append((i + 1, task))
        
        # Afficher les résultats
        if not results:
            print(f"Aucune tâche trouvée contenant '{args}'.")
            return
        
        print(f"\n{len(results)} tâches trouvées pour '{args}':")
        print("-" * 80)
        print(f"{'ID':<5} {'Titre':<40} {'Type':<15} {'Statut':<10}")
        print("-" * 80)
        
        for idx, task in results:
            title = task.get('title', 'Sans titre')
            task_type = task.get('type', 'N/A')
            status = task.get('status', 'N/A')
            
            # Tronquer le titre s'il est trop long
            if len(title) > 37:
                title = title[:34] + "..."
            
            print(f"{idx:<5} {title:<40} {task_type:<15} {status:<10}")
    
    def handle_ask_command(self, args):
        """Pose une question à l'IA."""
        if not args:
            print("Veuillez poser une question.")
            return
        
        print("Traitement de votre demande...")
        tasks = self.csv_manager.read_tasks()
        
        try:
            # Utiliser ask_question au lieu de query
            response = self.ai_service.ask_question(args, tasks)
            print("\nRéponse de l'IA:")
            print("-" * 80)
            print(response)
            print("-" * 80)
        except Exception as e:
            print(f"Erreur lors de la requête à l'IA: {str(e)}")
    
    def handle_plan_command(self, args):
        """Demande à l'IA de générer un plan de projet."""
        if not args:
            print("Veuillez fournir une description pour le plan.")
            return

        plan_description = args
        print("Génération d'un plan de projet...")
        
        try:
            plan = self.ai_service.generate_project_plan(plan_description)
            print("Plan généré par l'IA:")
            print("-" * 80)
            print(plan)
            print("-" * 80)
            
            choice = input("Souhaitez-vous ajouter ces tâches à votre projet? (o/n): ")
            if choice.lower() == 'o' or choice.lower() == 'oui':
                try:
                    tasks = self.ai_service.generate_tasks_from_plan(plan)
                    
                    # Afficher les tâches avant de les ajouter
                    print("\nTâches qui seront ajoutées:")
                    for i, task in enumerate(tasks, 1):
                        print(f"{i}. {task.get('title', 'Sans titre')} ({task.get('type', 'Type inconnu')})")
                    
                    confirm = input("\nConfirmer l'ajout de ces tâches? (o/n): ")
                    if confirm.lower() == 'o' or confirm.lower() == 'oui':
                        count = self.csv_manager.add_tasks_from_json(tasks)
                        print(f"{count} tâches ajoutées avec succès!")
                    else:
                        print("Ajout des tâches annulé.")
                except Exception as e:
                    print(f"Erreur lors du traitement du plan: {str(e)}")
                    
                    # Si l'erreur est liée au JSON, proposer de voir la réponse brute
                    if "JSON" in str(e):
                        show_raw = input("Voulez-vous voir la réponse brute de l'IA? (o/n): ")
                        if show_raw.lower() == 'o':
                            raw_response = self.ai_service.last_raw_response if hasattr(self.ai_service, 'last_raw_response') else "Non disponible"
                            print("\nRéponse brute:")
                            print("-" * 80)
                            print(raw_response[:500])  # Afficher les 500 premiers caractères
                            print("...")
                            print("-" * 80)
        except Exception as e:
            print(f"Erreur lors de la génération du plan: {str(e)}")
    
    def handle_export_command(self, args):
        """Exporte les tâches vers un autre fichier."""
        if not args:
            print("Veuillez spécifier le nom du fichier de destination.")
            return
        
        destination = args
        tasks = self.csv_manager.read_tasks()
        
        try:
            # Assurer un chemin absolu
            if not os.path.isabs(destination):
                destination = os.path.join(os.getcwd(), destination)
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(destination):
                confirm = input(f"Le fichier {destination} existe déjà. Voulez-vous l'écraser? (o/n): ")
                if confirm.lower() != 'o' and confirm.lower() != 'oui':
                    print("Exportation annulée.")
                    return
            
            # Créer un nouveau CSVManager pour le fichier de destination
            from data.csv_manager import CSVManager
            dest_manager = CSVManager(destination)
            
            # Écrire les tâches
            dest_manager.write_tasks(tasks)
            print(f"{len(tasks)} tâches exportées avec succès vers {destination}!")
            
        except Exception as e:
            print(f"Erreur lors de l'exportation: {str(e)}")