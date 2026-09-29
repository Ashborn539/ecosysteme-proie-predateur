# Écosystème Proie-Prédateur

Simulation d’un écosystème avec des proies, des prédateurs et des ressources, pilotée par un serveur Python et affichée via une interface JavaFX.

## Prérequis

- Python 3.10+  
- Java SDK 25  
- JavaFX SDK 25.0.1  
- `json-20240303.jar` (déjà présent dans le dépôt)

## Structure du projet

- `main.py` : lance la simulation et le serveur de données
- `DisplayClientFX.java` : client graphique JavaFX
- `agent.py`, `world.py`, `ressources.py`, `parametres.py` : logique métier de la simulation

## Lancement

### 1) Démarrer la simulation Python

```bash
python main.py
```

### 2) Lancer le client JavaFX

Configurer votre exécution Java avec les paramètres suivants :

- **Main class** : `DisplayClientFX`
- **VM options** :  
  `--module-path "C:\chemin\vers\javafx-sdk-25.0.1\lib" --add-modules javafx.controls,javafx.fxml`
- **Classpath** : inclure `json-20240303.jar`
- **Working directory** : dossier racine du dépôt

## Remarques

- Le client JavaFX se connecte localement au serveur Python sur `localhost:5000`.
- Adaptez les chemins locaux (JavaFX) selon votre environnement.
