"""
Auteur : Tylden Hounsa
Date de creation : 27/09/2025
Contenu : Parametres par defaut du monde et de ses agents
"""
DEFAULTS = {
    # Monde
    "world_width": 50,                      # largeur
    "world_height":50,                      # longeur
    "use_screen_dimentions": False,          # utilisation des dimensions de l'écran
    "send_frame": 0.2,                      # Frequence d'envois
    "sim_speed" : 4.5,                        # vitesse de base de la simulation 
    "cpu_breath_time" : 0.004,               # Temps de pause 
    "initial_sheep": 15,                     # nombre de mouton
    "initial_wolves": 3,                    # nombre de loup
    #Ressources 
    "initial_water_point": 20,               # Nombre de points d'eau
    "initial_grass_point": 10,            # Nombre de points de d'herbe
    "grass_regrowth_rate": 0.1,              # Chance (par frame) qu'une herbe repousse si le total est < initial
    "grass_regrowth" : True,
    # Mouton 
    "sheep_speed_walk": 0.8,                # vitesse de marche
    "sheep_speed_sprint": 1.5,              # Vitesse de course (inférieure à celle du loup)
    "sheep_energy_max": 100,                # energie max
    "sheep_hungry_threshold" : 80,           # Commence à chercher de la nourriture quand l'énergie est < 80%
    "sheep_vision_radius": 6,               # Rayon de vision du mouton (proie, donc très alerte)
    "sheep_vision_angle": 320.0,            # Angle de vision panoramique, réaliste pour une proie
    "sheep_flee_distance_threshold": 10,    # Distance à laquelle le mouton se sent en sécurité après avoir fui
    "sheep_energy_walk_cost": 0.35,         # depense energetique en marche 
    "sheep_energy_sprint_cost": 0.7,        # depense energetique en course
    # Loup
    "wolf_speed_walk": 0.7,                 # vitesse de marche
    "wolf_speed_sprint": 1.6,                # Vitesse de course (supérieure à celle du mouton)
    "wolf_energy_max": 120,                 # energie max
    "wolf_hungry_threshold" : 80,            # Commence à chasser quand l'énergie est < 80 (66% de 120)
    "wolf_vision_radius": 7,               # Rayon de vision du loup (prédateur, focus sur la proie)
    "wolf_vision_angle": 250.0,             # Angle de vision réaliste pour un prédateur
    "wolf_energy_walk_cost": 0.4,         # depense energetique en marche
    "wolf_energy_sprint_cost": 0.85,        # Le sprint est très coûteux, simule l'endurance limitée
    "wolf_exploration_radius": 2,           # Rayon de découverte autour de la position (pour la mémoire)
}
