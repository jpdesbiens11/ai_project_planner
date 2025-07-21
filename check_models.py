# check_models.py
import requests
import json

def get_installed_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("Modèles Ollama installés:")
            print("-" * 50)
            print(f"{'Nom':<25} {'Tag':<15} {'Taille':<15}")
            print("-" * 50)
            for model in models:
                name = model.get('name', 'N/A')
                tag = model.get('tag', 'default')
                size = model.get('size', 'N/A')
                # Convertir la taille en MB ou GB pour une meilleure lisibilité
                if isinstance(size, int):
                    if size > 1024*1024*1024:  # Plus de 1 GB
                        size_str = f"{size/(1024*1024*1024):.2f} GB"
                    else:
                        size_str = f"{size/(1024*1024):.2f} MB"
                else:
                    size_str = str(size)
                print(f"{name:<25} {tag:<15} {size_str:<15}")
        else:
            print(f"Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erreur lors de la connexion à Ollama: {str(e)}")
        print("Assurez-vous que le service Ollama est en cours d'exécution.")

if __name__ == "__main__":
    get_installed_models()