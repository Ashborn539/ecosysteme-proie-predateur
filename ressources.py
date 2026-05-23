"""
Auteur : Tylden Hounsa
Date de creation : 27/09/2025
Contenu : Classe des ressources : grass et water
    -
"""

# Creation d'une classe ressources
class ressource:
    """
    - ressource.x()
    - ressource.y()
    - ressource.uid()
    """
    def __init__(self, x, y, world, uid):
        self.x = x
        self.y = y
        self.world = world
        self.uid = uid

class grass(ressource):
    """
    - grass.x()
    - grass.y()
    - grass.uid()
    """
    def __init__(self, x, y, world):
        super().__init__(
            x=x, 
            y=y, 
            world=world,
            uid=None # UID assigné par le monde
        )

class water(ressource):
    """
    - water.x()
    - water.y()
    - water.uid()
    """
    def __init__(self, x, y, world):
        super().__init__(
            x=x, 
            y=y, 
            world=world,
            uid=None # UID assigné par le monde
        )