"""
Auteur : Tylden Hounsa
Date de creation : 02/10/2025
Contenu : Programme principal 
Modificatons : 
    - 09/10/2025 : Ajouts des fonctions initialize_world_randomly
                    et modification de la foncion 
    - 11/10/2025 : Ajouts du locket dans les fonctions 
    - 12/10/2025 : Creation d'une commande qui arrete la similation 
"""

import agent
import world
import ressources
from parametres import DEFAULTS
import random
import time
import socket
import json
from pynput import keyboard
import tkinter as tk
import csv

# INITIALISATION 
world = world.World()
sim_flag = True

#------------------------------------------------------------------------------------------------------------
if DEFAULTS["use_screen_dimentions"]:
    # --- Détermination dynamique des dimensions du monde ---
    # Taille en pixels d'une case du monde (à synchroniser avec le client Java)
    CELL_PIXEL_SIZE = 15

    try:
        # Utiliser tkinter pour obtenir la résolution de l'écran
        root = tk.Tk()
        root.withdraw() # Cacher la fenêtre principale de tkinter
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()

        # Calculer les dimensions du monde pour qu'il s'adapte à l'écran
        # On prend une marge pour la barre de titre de la fenêtre et la barre des tâches
        new_world_width = int((screen_width * 0.98) / CELL_PIXEL_SIZE)
        new_world_height = int((screen_height * 0.90) / CELL_PIXEL_SIZE)

        # Mettre à jour les dimensions dans les paramètres avant de créer le monde
        DEFAULTS["world_width"] = new_world_width
        DEFAULTS["world_height"] = new_world_height
        print(f"Dimensions de l'écran détectées : {screen_width}x{screen_height}. Monde ajusté à {new_world_width}x{new_world_height} cases.")
    except tk.TclError:
        print("Impossible de détecter la taille de l'écran (pas d'environnement graphique). Utilisation des dimensions par défaut.")
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

# Initialisation du monde avec des agents a des positions aléatoires 
# Creation des agents et ressources de base 
for _ in range(DEFAULTS["initial_sheep"]):
    # Creation des agent sheep a des positions aléatoires (indices valides de 0 à width-1)
    x = random.uniform(0, world.width)
    y = random.uniform(0, world.height)
    new_sheep = agent.Sheep(x, y, world=world)  #Ajout de l'agent a la liste des agents du monde
    world.add_agent(new_sheep)
    new_sheep.start() # Démarrage du thread du mouton

for _ in range(DEFAULTS["initial_wolves"]):
    # Creation des agenst loup a des positions aléatoires
    x = random.uniform(0, world.width)
    y = random.uniform(0, world.height)
    new_wolf = agent.Wolf(x, y, world)# Ajout de l'agent a la liste des agents du monde
    world.add_agent(new_wolf)
    new_wolf.start() # Démarrage du thread des loups 

for _ in range(DEFAULTS["initial_water_point"]):
    # Creation des points d'eau a des positions aléatoires
    x=random.uniform(0, world.width)
    y=random.uniform(0, world.height - 1)
    new_water = ressources.water(x, y, world=world )
    # Ajout de la ressource a la liste des ressouces du monde 
    world.add_resource(new_water)

for _ in range(DEFAULTS["initial_grass_point"]):
    # Creation des points de sol a des positions aléatoires
    x=random.uniform(0, world.width)
    y=random.uniform(0, world.height - 1)
    new_grass = ressources.grass(x, y, world=world ) # Ajout de la ressource a la liste des ressources
    world.add_resource(new_grass)


# Fonction pour gérer la touche de fin de la simulation et d'accélération 
def on_press(key):
    """Fonction appelée à chaque pression de touche."""
    global sim_flag
    try:
        key_char = key.char
    except AttributeError:
        return # Gère les touches spéciales (Shift, Ctrl, etc.)

    if key_char == 'q':
        print("Touche 'q' pressée. Arrêt de la simulation...")
        sim_flag = False
        return False  # Arrête le listener
    elif key_char == '+':
        # On utilise un verrou pour modifier la vitesse en toute sécurité
        with world.lock:
            world.simulation_speed = min(world.simulation_speed * 1.2, 90) # Augmente la vitesse de 20%, avec un maximum
        print(f"Vitesse de simulation : {world.simulation_speed:.2f}x")
    elif key_char == '-':
        with world.lock:
            world.simulation_speed = max(world.simulation_speed / 1.2, 0.1) # Diminue la vitesse de 20%, avec un minimum de 0.1x
        print(f"Vitesse de simulation : {world.simulation_speed:.2f}x")

# Creation d'un fichier json contenant les agents et leurs position dans le monde 
def get_world_state_as_json():
    """Retourne une version JSON du monde (agents + ressources)."""
    with world.lock:
        data = {
            "width": world.width,
            "height": world.height,
            "agents": [
                {
                    "type": "Sheep" if isinstance(a, agent.Sheep) else "Wolf",
                    "x": a.x,
                    "y": a.y,
                    "uid": str(a.uid),
                }
                for a in world.agents.values()
            ],
            "resources": [
                {
                    "type": "Water" if isinstance(r, ressources.water) else "Grass",
                    "x": r.x,
                    "y": r.y,
                    "uid": str(r.uid)
                }
                for r in world.resources.values()
            ]
        }
        return json.dumps(data)


# ----- Serveur socket pour communication avec le client Java ------
HOST = 'localhost'
PORT = 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"Serveur Python en attente de connexion sur {HOST}:{PORT}...")
# Attendre que le client Java se connecte
conn, addr = server_socket.accept()
print(f"Client Java connecté depuis {addr}")

# Démarrage du listener de clavier dans un thread séparé
listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
# Boucle principale de la simulation
    while sim_flag :
        if DEFAULTS["grass_regrowth"]:
            # Régénération de l'herbe 
            with world.lock:
                # Compte le nombre actuel de points d'herbe
                current_grass_count = sum(1 for r in world.resources.values() if isinstance(r, ressources.grass))
        
            # Si le nombre d'herbes est inférieur au nombre initial, on peut en faire repousser
            if current_grass_count < DEFAULTS["initial_grass_point"]:
                # Chaque frame a une petite chance de faire repousser une herbe
                if random.random() < DEFAULTS["grass_regrowth_rate"]:
                    x = random.uniform(0, world.width)
                    y = random.uniform(0, world.height - 1)
                    new_grass = ressources.grass(x, y, world=world)
                    world.add_resource(new_grass)

        # Envoi de l'état du monde en JSON au client Java
        try:
            world_json = get_world_state_as_json()
            # On ajoute un retour à la ligne pour que le client Java puisse lire ligne par ligne
            conn.sendall((world_json + "\n").encode('utf-8'))

        except (BrokenPipeError, ConnectionResetError):
            print("La connexion avec le client a été perdue. Arrêt de la simulation.")
            sim_flag = False # Arrêter la simulation si le client se déconnecte

        # La pause est inversement proportionnelle à la vitesse de simulation pour contrôler la cadence
        time.sleep(DEFAULTS["send_frame"] / world.simulation_speed)

finally:
    # Nettoyage à la fin de la simulation
    print("Arrêt des threads des agents...")   
    # Creation d'une liste des agents  
    agents_to_stop = list(world.agents.values())
    # Arrêt des threads des agents
    for agent_instance in agents_to_stop:
        agent_instance.is_alive_flag = False
    # Attend que tous les autres agents 
    for agent_instance in agents_to_stop:
        agent_instance.join()

# Affichage d'un message à la fin de la simulation 
print("Tous les threads ont été arrêtés.")
# Fermeture de la connexion et du serveur
conn.close()
server_socket.close()
listener.stop()
print("Serveur fermé.")