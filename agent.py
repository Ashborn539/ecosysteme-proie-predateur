"""
Auteur : Tylden Hounsa
Date de création : 27/09/2025
Contenu : Classe principale "Agent" et sous-classes "Sheep" (mouton) et "Wolf" (loup) pour une simulation avec déplacement continu.
"""

import threading
import math
import time
import random
import heapq
from parametres import DEFAULTS

class Agent(threading.Thread):
    """
    Classe de base pour un agent (mouton ou loup). Hérite de threading.Thread.
    Contient les attributs et méthodes généraux.
    """
    def __init__(self, x, y, energy, world, uid=None):
        super().__init__()
        self.x = x
        self.y = y
        self.energy = energy
        self.world = world
        self.uid = uid
        self.is_alive_flag = True  # devient False pour arrêter le thread
        self.path = []     # chemin actuel (liste de points (x,y))
        self.path_index = 0
        self.direction = (1, 0) # Direction de l'agent (vecteur normalisé)
        self.simulation_speed_to_print = 1

    def run(self):
        """Boucle principale de l’agent. Défini dans les sous-classes."""
        raise NotImplementedError("Run doit être implémenté par les sous-classes")


class Sheep(Agent):
    """
    Classe Sheep (mouton)
    """
    def __init__(self, x, y, world):
        super().__init__(x, y, DEFAULTS["sheep_energy_max"], world)
        # Paramètres spécifiques au mouton
        self.speed_walk = DEFAULTS["sheep_speed_walk"]
        self.speed_sprint = DEFAULTS["sheep_speed_sprint"]
        self.vision_radius = DEFAULTS["sheep_vision_radius"]
        self.vision_angle = DEFAULTS["sheep_vision_angle"]
        self.hungry_threshold = DEFAULTS["sheep_hungry_threshold"]
        self.energy_cost_walk = DEFAULTS["sheep_energy_walk_cost"]
        self.energy_cost_sprint = DEFAULTS["sheep_energy_sprint_cost"]

    def run(self): 
        """
        Boucle principale du mouton :
        - Si la faim est faible, chercher de l'herbe.
        - Si un loup est visible, fuir vers un point aléatoire (en courant).
        - Se déplacer le long du chemin calculé, mettre à jour la position et l’énergie.
        """
        while self.is_alive_flag:
            # Déterminer la cible selon l'état
            target = None
            #-------------------------------------------------------------------------------------------
            # 1. Si un loup est proche, fuir : définir une position aléatoire hors du rayon du loup
            current_speed = self.speed_walk
            closest_wolf = None
            min_wolf_dist = float('inf')
            with self.world.lock:
                # Copie du de la liste des agents pour éviter les problèmes de concurrence
                agents_list = list(self.world.agents.values())
            
            # Parcourir la liste des agents et inorer ceux qui sont pas de la classe voulu
            for possible_wolf in agents_list:
                if not isinstance(possible_wolf, Wolf):
                    continue
                # Calculer la distance entre la cible et l'agent
                dist = self.world.distance((self.x, self.y), (possible_wolf.x, possible_wolf.y))
                # Si la cible est prochet et dans le champ de vision
                if dist < self.vision_radius and self.world.within_vision(self, possible_wolf):
                    if dist < min_wolf_dist:
                        min_wolf_dist = dist
                        closest_wolf = possible_wolf
            
            if closest_wolf: # Si un loup est proche
                # Fuir fuire le loup vers une position aléatoir eopposée a lui
                angle = math.atan2(self.y - closest_wolf.y, self.x - closest_wolf.x)
                run_distance = random.uniform(self.vision_radius, self.vision_radius * 1.5)
                # Calculer la position aléatoire
                target_x = self.x + run_distance * math.cos(angle)
                target_y = self.y + run_distance * math.sin(angle)
                # S'assurer que la case cible reste dans le monde
                target_x = max(0, min(self.world.width - 1, target_x))
                target_y = max(0, min(self.world.height - 1, target_y))
                target = (target_x, target_y)
                # Charger la vitesse de déplacement
                current_speed = self.speed_sprint

            #-------------------------------------------------------------------------------------------
            else: # Si un loup n'est pas proche
                # 2 . Sinon, si faim critique, chercher de l'herbe la plus proche
                if self.energy < self.hungry_threshold:
                    closest_grass = None
                    min_grass_dist = float('inf')
                    with self.world.lock:
                        # Itérer sur une copie de la liste des ressources
                        resources_list = list(self.world.resources.values())
                    
                    for resource in resources_list: # on parcours la liste de ressources 
                        # On cherche la ressource de classe grass la plus proche
                        if type(resource).__name__ == 'grass':
                            dist = self.world.distance((self.x, self.y), (resource.x, resource.y))
                            if dist < min_grass_dist:
                                min_grass_dist = dist # On met a jour la distance la plus proche
                                closest_grass = (resource.x, resource.y) # On met a jour la ressource la plus proche
                    # Si il trouve de l'herbe proche de lui 
                    if closest_grass:
                        target = closest_grass # On met a jour la cible
                        current_speed = self.speed_walk # On met a jour la vitesse de déplacement

            #-------------------------------------------------------------------------------------------
            # 3 . Sinon, se promener aléatoirement si plus rien à faire
            if not target and (not self.path or self.path_index >= len(self.path)): # Si aucune cible et aucun chemin
                # Choisir un point aléatoire dans le monde comme nouvelle cible
                rx = random.uniform(0, self.world.width)
                ry = random.uniform(0, self.world.height)
                target = (rx, ry)
                current_speed = self.speed_walk

            # Calculer le chemin si une nouvelle cible est définie
            # On recalcule le chemin seulement si on a une nouvelle cible, ou si on a fini le chemin précédent.
            if target and (not self.path or self.path_index >= len(self.path)):
                self.path = self.world.astar((self.x, self.y), target)
                self.path_index = 0

            # Déplacement : avancer d'un pas vers le prochain point du chemin
            if self.path and self.path_index < len(self.path):
                # Prochain point
                nx, ny = self.path[self.path_index]
                # Calcule du vecteur de direction vers le point de passage 
                dx = nx - self.x
                dy = ny - self.y
                # Calcule de la distance jusqua'au poinr de passage 
                dist_to_node = math.hypot(dx, dy)
                
                # Le pas de déplacement est proportionnel à la vitesse.
                # La vitesse de simulation globale est gérée par la boucle principale dans main.py
                step = current_speed * 0.01 # Facteur d'ajustement pour un mouvement fluide

                # Si on est très proche du point 
                if dist_to_node <= step: # or dist_to_node < 1e-6:
                    # Arrivé au nœud suivant
                    self.x = nx
                    self.y = ny
                    self.path_index += 1 # On vise ensuite le point de passage suivant 
                    # Si c'était de l'herbe, la manger
                    with self.world.lock:
                        eaten_resource = None
                        for resource in self.world.resources.values():
                            if type(resource).__name__ == 'grass' and self.world.distance((self.x, self.y), (resource.x, resource.y)) < 1.0:
                                eaten_resource = resource
                                break
                        if eaten_resource:
                            self.world.remove_resource(eaten_resource)
                            self.energy = min(self.energy + 30, DEFAULTS["sheep_energy_max"])
                else: # Si on est pas proche du point 
                    # On avance partiellement et pas à pas vers (nx,ny)
                    # On indque le Pourcentage de déplacement a effectuer sur chaque axe pour atteindre le point node 
                    self.x += (dx / dist_to_node) * step
                    self.y += (dy / dist_to_node) * step
                    # Mettre à jour la direction
                    self.direction = (dx / dist_to_node, dy / dist_to_node)
                
                # Dépenser l'énergie selon le mouvement
                cost = self.energy_cost_sprint if current_speed == self.speed_sprint else self.energy_cost_walk
                self.energy -= cost * step
                if self.energy <= 0:
                    # Mort de faim
                    self.is_alive_flag = False

            # La cadence de la simulation est gérée par la boucle principale.
            # Le sleep est inversement proportionnel à la vitesse de simulation
            time.sleep(DEFAULTS["cpu_breath_time"] / self.world.simulation_speed)# Sleep pour faire respirer le processeur

        # Fin du thread mouton, on le retire du monde
        with self.world.lock:
            if self.uid in self.world.agents:
                self.world.remove_agent(self)

class Wolf(Agent):
    """
    Classe Wolf (loup). Cherche à chasser les moutons, gère la faim.
    Possède une mémoire des emplacements qu'il a visités.
    """
    def __init__(self, x, y, world):
        super().__init__(x, y, DEFAULTS["wolf_energy_max"], world)
        # Paramètres spécifiques au loup
        self.speed_walk = DEFAULTS["wolf_speed_walk"]
        self.speed_sprint = DEFAULTS["wolf_speed_sprint"]
        self.vision_radius = DEFAULTS["wolf_vision_radius"]
        self.vision_angle = DEFAULTS["wolf_vision_angle"]
        self.hungry_threshold = DEFAULTS["wolf_hungry_threshold"]
        self.energy_cost_walk = DEFAULTS["wolf_energy_walk_cost"]
        self.energy_cost_sprint = DEFAULTS["wolf_energy_sprint_cost"]
        self.target_agent = None
        
        # Système de mémoire : carte des cellules connues
        # Utilise un dictionnaire {(x, y): timestamp} pour stocker les cellules visitées
        self.known_map = set()  # Ensemble des cellules (x, y) connues (coordonnées discrètes)
        self.exploration_radius = DEFAULTS.get("wolf_exploration_radius", 2)  # Rayon de découverte autour de la position actuelle
        
        # Marque la position initiale comme connue
        self.mark_area_as_known(x, y)

#-----------------------------COEUR DES DEPLACEMENTS DU LOUP -------------------------------------------

    def mark_as_known(self, x, y):
        """
        Marque une cellule (coordonnées discrètes) comme connue.
        """
        cell_x = int(x)
        cell_y = int(y)
        # Vérifie que la cellule est dans les limites du monde
        if 0 <= cell_x < self.world.width and 0 <= cell_y < self.world.height:
            self.known_map.add((cell_x, cell_y))
    
    def mark_area_as_known(self, x, y):
        """
        Marque une zone autour de la position (x, y) comme connue.
        Utilise exploration_radius pour découvrir les cellules voisines.
        """
        center_x = int(x)
        center_y = int(y)
        for dx in range(-self.exploration_radius, self.exploration_radius + 1):
            for dy in range(-self.exploration_radius, self.exploration_radius + 1):
                cell_x = center_x + dx
                cell_y = center_y + dy
                # Vérifie que la cellule est dans les limites du monde
                if 0 <= cell_x < self.world.width and 0 <= cell_y < self.world.height:
                    self.known_map.add((cell_x, cell_y))
    
    def is_known(self, x, y):
        """
        Vérifie si une cellule (coordonnées discrètes) est connue.
        """
        cell_x = int(x)
        cell_y = int(y)
        return (cell_x, cell_y) in self.known_map
    
    def get_known_positions(self):
        """
        Retourne une liste de toutes les positions connues (coordonnées flottantes au centre des cellules).
        """
        return [(x + 0.5, y + 0.5) for x, y in self.known_map]
    
    def get_random_known_position(self):
        """
        Retourne une position aléatoire parmi les positions connues.
        Retourne None si aucune position n'est connue.
        """
        if not self.known_map:
            return None
        x, y = random.choice(list(self.known_map))
        # Retourner le centre de la cellule pour un mouvement plus fluide
        return (x + 0.5, y + 0.5)
    
    def astar_memory(self, start:tuple[float, float], goal:tuple[float, float]):
        """
        Version de A* qui se déplace uniquement dans les zones connues.
        Si le but est inconnu, il cherche un chemin vers le point connu le plus proche du but.
        """
        start_node = (int(start[0]), int(start[1]))
        goal_node = (int(goal[0]), int(goal[1]))
        
        # Si le but est inconnu, chercher le point connu le plus proche du but
        if not self.is_known(goal[0], goal[1]):
            # Trouver la cellule connue la plus proche de la cible 
            closest_known = None
            min_dist = float('inf')
            for known_x, known_y in self.known_map:
                dist = math.hypot(known_x - goal_node[0], known_y - goal_node[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_known = (known_x, known_y)
            if closest_known: # definition de cette case comme cible 
                goal_node = closest_known
            else:
                # Aucune zone connue, retourner un chemin vide
                return []
        
        # Structures de données pour A*
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        
        def heuristic(a, b):
            return math.hypot(a[0] - b[0] , a[1] - b[1])
        
        f_score = {start_node: heuristic(start_node, goal_node)}
        visited = set()
        
        # Voisins (8 directions)
        neighbors = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal_node:
                # Reconstruire le chemin depuis goal vers start
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_node)
                path.reverse()
                # Ajout de la cible flottante exacte comme dernière étape pour un mouvement précis
                path.append(goal)
                return path
            
            visited.add(current)
            
            # Explorer les voisins
            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)

                # Vérifier limites du monde
                if 0 <= neighbor[0] < self.world.width and 0 <= neighbor[1] < self.world.height:
                    # Vérifier si la cellule est praticable (pas d'eau)
                    if not self.world.is_cell_traversable(neighbor[0], neighbor[1]):
                        continue  # Ignorer les cellules contenant de l'eau (impraticables)
                    
                    # Ignorer les cellules inconnues
                    if not self.is_known(neighbor[0], neighbor[1]):
                        continue
                    
                    move_cost = math.hypot(dx, dy)
                    tentative_g = g_score[current] + move_cost
                    
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        g_score[neighbor] = tentative_g
                        f = tentative_g + heuristic(neighbor, goal_node)
                        f_score[neighbor] = f
                        came_from[neighbor] = current
                        if neighbor not in visited:
                            heapq.heappush(open_set, (f, neighbor))
        
        # Aucun chemin trouvé
        return []
#--------------------------------------------------------------------------------------------------------

    def run(self):
        """
        Boucle principale du loup :
        - Si la faim est faible et qu'un mouton est à portée, chasser le mouton le plus proche.
        - Sinon, errer.
        - Se déplacer le long du chemin vers le mouton, et s'il l'attrape, le manger.
        """
        while self.is_alive_flag:
            target_pos = None
            current_speed = self.speed_walk

            # 1) Chasse : rechercher le mouton le plus proche visible si affamé
            if self.energy < self.hungry_threshold:
                closest_sheep = None
                min_sheep_dist = float('inf')
                with self.world.lock:
                    agents_list = list(self.world.agents.values())
                
                for possible_sheep in agents_list:
                    if not isinstance(possible_sheep, Sheep):
                        continue
                    dist = self.world.distance((self.x, self.y), (possible_sheep.x, possible_sheep.y))
                    if dist < self.vision_radius and self.world.within_vision(self, possible_sheep):
                        if dist < min_sheep_dist:
                            min_sheep_dist = dist
                            closest_sheep = possible_sheep
                
                if closest_sheep:
                    # Vérifier si un chemin praticable existe vers le mouton (qui évite l'eau)
                    sheep_pos = (closest_sheep.x, closest_sheep.y)
                    # Essayer de trouver un chemin dans les zones connues
                    test_path = self.astar_memory((self.x, self.y), sheep_pos)
                    
                    if test_path:
                        # Un chemin connu existe qui évite l'eau, on peut chasser
                        target_pos = sheep_pos
                        self.target_agent = closest_sheep
                        current_speed = self.speed_sprint
                    else:
                        # Aucun chemin connu, on ne peut pas chasser
                        self.target_agent = None
                        target_pos = None
                else:
                    self.target_agent = None

            # 2) Sinon, errer aléatoirement vers une position connue
            if not target_pos and (not self.path or self.path_index >= len(self.path)):
                # Choisir une position aléatoire parmi les zones connues
                known_target = self.get_random_known_position()
                if known_target:
                    target_pos = known_target
                    current_speed = self.speed_walk
                else:
                    # Si aucune zone connue (ne devrait pas arriver), explorer autour de la position actuelle
                    target_pos = None

            # Si on chasse, mettre à jour la cible avec la position actuelle du mouton
            # (doit être fait après l'errance pour avoir la priorité)
            if self.target_agent:
                target_pos = (self.target_agent.x, self.target_agent.y)

            # Recalculer le chemin A* si la cible est définie et si le chemin est vide ou fini
            if target_pos and (not self.path or self.path_index >= len(self.path)):
                self.path = self.astar_memory((self.x, self.y), target_pos)
                # compteur pour parcourir la liste des chemins possibles 
                self.path_index = 0
                
                # Si aucun chemin n'a été trouvé et qu'on chassait, arrêter la chasse
                if not self.path and self.target_agent:
                    self.target_agent = None
                    target_pos = None

            # Déplacement : avancer d'un pas vers le prochain point du chemin
            if self.path and self.path_index < len(self.path):
                # Prochain point
                nx, ny = self.path[self.path_index]
                # Calculer direction
                dx = nx - self.x
                dy = ny - self.y
                dist_to_node = math.hypot(dx, dy)
                
                # Le pas effectué est proportionelle a la vitesse de déplacement
                step = current_speed * 0.01 # Facteur d'ajustement pour un mouvement fluide

                # Si on peut atteindre ou dépasser le point
                if dist_to_node <= step or dist_to_node < 1e-6:
                    # Arrivé au nœud suivant
                    self.x = nx
                    self.y = ny
                    self.path_index += 1
                    # Marquer la zone autour de la nouvelle position comme connue
                    self.mark_area_as_known(self.x, self.y)
                else:
                    # Avancer partiellement vers (nx,ny)
                    self.x += (dx / dist_to_node) * step
                    self.y += (dy / dist_to_node) * step
                    # Mettre à jour la direction
                    self.direction = (dx / dist_to_node, dy / dist_to_node)
                    # Marquer la zone autour de la position actuelle comme connue (découverte progressive)
                    self.mark_area_as_known(self.x, self.y)
                
                # Si on attrape un mouton
                if self.target_agent and self.target_agent.is_alive_flag:
                    if self.world.distance((self.x, self.y), (self.target_agent.x, self.target_agent.y)) < 1.0:
                        with self.world.lock:
                            # On vérifie si le mouton est toujours dans le monde avant de le tuer
                            if self.target_agent.uid in self.world.agents:
                                self.target_agent.is_alive_flag = False # Signale au thread du mouton de s'arrêter
                                self.world.remove_agent(self.target_agent) # Retire le mouton du dictionnaire
                            # Le loup regagne de l'énergie
                            self.energy = min(self.energy + 50, DEFAULTS["wolf_energy_max"])
                            # La chasse est terminée
                            self.target_agent = None
                            self.path = []
                            self.path_index = 0

                # Dépenser l'énergie selon le mouvement
                cost = self.energy_cost_sprint if current_speed == self.speed_sprint else self.energy_cost_walk
                self.energy -= cost * step
                if self.energy <= 0:
                    # Mort de faim
                    self.is_alive_flag = False

            # La cadence de la simulation est gérée par la boucle principale.
            # Le sleep est inversement proportionnel à la vitesse de simulation
            time.sleep(DEFAULTS["cpu_breath_time"] / self.world.simulation_speed)

        # Fin du thread loup, on le retire du monde
        with self.world.lock:
            if self.uid in self.world.agents:
                self.world.remove_agent(self)
