"""
Auteur : Tylden Hounsa
Date de creation : 27/09/2025
Contenu : classe principale "World"
"""
from parametres import DEFAULTS
import uuid
import threading
import heapq
import math


class World:
    """
    - world.width()
    - world.height()
    - world.add_agent()
    - world.remove_agent()
    - world.add_resource()
    - world.remove_resource()
    - world.add_obstacle()
    - world.remove_obstacle()
    """
    # INITIALISATION 
    def __init__(self):
        self.width = DEFAULTS["world_width"] # Largeur
        self.height = DEFAULTS["world_height"] # Longueur
        # Declaration des listes
        self.agents = {}
        self.resources = {}
        # Verrou ré-entrant pour synchroniser l'accès au monde.
        self.lock = threading.RLock()
        self.simulation_speed = DEFAULTS["sim_speed"] # Multiplicateur de vitesse de la simulation
        
    # METHODES 
    # Pour les Agents 
    def add_agent(self, agent):
        """
        Ajoute un agent a la liste des agents (uid, agent)
        """
        with self.lock:
            uid = uuid.uuid4()
            agent.uid = uid  # Assigne un UID unique à l'agent
            self.agents[uid] = agent
    
    def remove_agent(self, agent):
        """
        Supprime un agent de la liste des agents
        """
        with self.lock:
            if agent.uid in self.agents:
                del self.agents[agent.uid]
    
    # Pour les ressources
    def add_resource(self, resource):
        """
        Ajoute une ressource au monde.
        Génère un UID unique pour la ressource et l'ajoute au dictionnaire des ressources.
        """
        with self.lock:
            uid = uuid.uuid4()  # Génération d'un identifiant unique
            resource.uid = uid 
            self.resources[uid] = resource

    def remove_resource(self, resource):
        """
        Supprime une ressource de la liste des ressources
        """
        with self.lock:
            if resource.uid in self.resources:
                del self.resources[resource.uid]

    def distance (self, a, b):
        """
        Calcule la distance euclidienne entre deux points (a et b).
        Chaque point est un tuple (x, y).
        """
        return ((a[0] - b[0])**2 + (a[1] - b[1])**2)**0.5
    
    def has_water_at(self, x, y):
        """
        Vérifie si une cellule (coordonnées discrètes) contient de l'eau.
        Retourne True si de l'eau est présente à cette position.
        """
        cell_x = int(x)
        cell_y = int(y)
        # Vérifie toutes les ressources d'eau pour voir si l'une est à cette position
        # Utilise le verrou pour accéder en toute sécurité à la liste des ressources
        with self.lock:
            for resource in self.resources.values():
                if type(resource).__name__ == 'water':
                    # Vérifie si l'eau est dans cette cellule (avec une tolérance)
                    water_x = int(resource.x)
                    water_y = int(resource.y)
                    if water_x == cell_x and water_y == cell_y:
                        return True
        return False
    
    def is_cell_traversable(self, x, y):
        """
        Vérifie si une cellule est praticable (pas d'eau).
        Retourne False si la cellule contient de l'eau (impraticable).
        Les autres types de terrain sont considérés comme praticables.
        """
        return not self.has_water_at(x, y)
    
    # --- 5. ALGORITHME A* (PATHFINDING) ---
    def astar(self, start, goal):
        """
        Algorithme A* pour trouver un chemin de start vers goal sur la grille du monde.
        start et goal sont des tuples (x,y) en coordonnées flottantes.
        On convertit ces positions en nœuds de grille entiers, calcule le chemin,
        puis on renvoie la liste de nœuds (x, y) aboutissant au but. Retourne [] si impossible.
        """
        # Conversion des coordonnées flottantes de départ et d'arrivée en nœuds de grille entiers
        start_node = (int(start[0]), int(start[1]))
        goal_node  = (int(goal[0]), int(goal[1]))
        
        # Initialisation des structures de données pour l'algorithme A*
        open_set = []
        # open_set est un tas-min (min-heap)
        # heapq.heappush(tas, élément) 
        heapq.heappush(open_set, (0, start_node))  # (f_score, nœud)
        
        # came_from : dictionnaire pour reconstruire le chemin. came_from[nœud] = nœud_précédent
        came_from = {}
        # g_score : coût réel du chemin du start_node au nœud actuel
        g_score = {start_node: 0}

        # Heuristique : distance de Manhattan ou Euclidienne
        def heuristic(a, b):
            return math.hypot(a[0] - b[0] , a[1] - b[1])
        
        # f_score : coût total estimé du chemin (g_score + heuristique)
        f_score = {start_node: heuristic(start_node, goal_node)}
        # visited : ensemble des nœuds déjà évalués 
        visited = set()

        # Voisins (8 directions)
        neighbors = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

        # Boucle principale de l'algorithme A*
        while open_set:
            # Récupération du nœud avec le plus petit f_score de l'open_set
            _, current = heapq.heappop(open_set) # Retire et renvoie l'élément le plus petit.
            
            # Vérification si le nœud actuel est le nœud d'arrivée
            if current == goal_node:
                # Reconstruction du chemin en remontant de goal_node à start_node via came_from
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_node)
                path.reverse()
                # Ajout de la cible flottante exacte comme dernière étape pour un mouvement précis
                path.append(goal)
                return path
            
            # Ajout du nœud actuel à l'ensemble des nœuds visités
            visited.add(current)

            # Exploration des nœuds voisins du nœud actuel
            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy) # Explorer les voisins
                
                # Vérifier limites du monde
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height: #Si on est dans les limites du monde 
                    # Vérifier si la cellule est praticable (pas d'eau)
                    if not self.is_cell_traversable(neighbor[0], neighbor[1]):
                        continue  # Ignorer les cellules contenant de l'eau

                    # Calcul du coût g_score provisoire pour atteindre le voisin
                    tentative_g = g_score[current] + math.hypot(dx, dy)
                    
                    # Si le voisin n'a jamais été atteint ou si un chemin plus court est trouvé
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        g_score[neighbor] = tentative_g  # Mise à jour du g_score du voisin
                        f = tentative_g + heuristic(neighbor, goal_node)
                        f_score[neighbor] = f
                        came_from[neighbor] = current  # Enregistre le chemin : le voisin a été atteint depuis le nœud actuel
                        
                        # Si le voisin n'a pas encore été visité, l'ajouter à l'open_set
                        if neighbor not in visited:
                            heapq.heappush(open_set, (f, neighbor))
        # Aucun chemin trouvé
        return []
    
    def within_vision(self, agent, target):
        """
        Indique si la 'target' est dans le champ de vision de l'agent (mouton ou loup).
        La target est un tuple (x,y) ou un agent (avec .x,.y).
        On vérifie le rayon et l'angle de vision.
        """
        # Obtenir la position de la cible
        tx, ty = (target.x, target.y) if hasattr(target, 'x') else (target[0], target[1])
        dx = tx - agent.x
        dy = ty - agent.y
        dist = math.hypot(dx, dy)

        # Vérifier si la cible est dans le rayon de vision
        if dist > agent.vision_radius:
            return False

        # Vérifier si la cible est dans le cône de vision
        # Calcul du vecteur directionnel de l'agent vers la cible
        target_vector = (dx, dy)

        # Récupération du vecteur de direction actuel de l'agent
        agent_direction = agent.direction

        # Calcul du produit scalaire entre le vecteur de direction de l'agent et le vecteur vers la cible
        dot_product = agent_direction[0] * target_vector[0] + agent_direction[1] * target_vector[1]
        # Calcul des magnitudes
        mag_agent_dir = math.hypot(*agent_direction)
        # mag_target_vec est 'dist'

        # Calcul de l'angle en radians, puis conversion en degrés
        # Ajout d'un petit epsilon (1e-6) pour éviter une division par zéro si dist ou mag_agent_dir est nul
        angle_rad = math.acos(dot_product / (mag_agent_dir * dist + 1e-6))
        angle_deg = math.degrees(angle_rad)

        return angle_deg <= (agent.vision_angle / 2)