/*
Auteur : Tylden Hounsa
Date de création : 02/11/2025
Contenu : Interface graphique de la simulation
*/

import javafx.application.Application;
import javafx.application.Platform;
import javafx.scene.Scene;
import javafx.scene.Group;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.scene.shape.Rectangle;
import javafx.stage.Stage;
import org.json.*;
import java.io.*;
import java.net.Socket;

public class DisplayClientFX extends Application {

    // declaration des variables
    private static final String HOST = "localhost"; // adresse ip
    private static final int PORT = 5000; // port de connection
    private static final String worldBackground = "BLACK"; // couleur de fond de la grille
    private static final String sheep_color = "WHITE";
    private static final String wolf_color = "#b30000";
    private static final String water_color = "#4da6ff";
    private static final String grass_color = "#7ED957";

    // Mise en place du monde 
    private static final int WIDTH = 600, HEIGHT = 600;
    private Group root;
    private double worldWidth = 50.0, worldHeight = 50.0; // Par défaut, peuvent être mis à jour depuis JSON

    @Override
    public void start(Stage stage) {
        root = new Group();
        Scene scene = new Scene(root, WIDTH, HEIGHT, Color.valueOf(worldBackground)); // Mise en place de la scene
        stage.setTitle("Simulation Sheep-Wolf"); //Titre de la fenêtre
        stage.setScene(scene); // Ajout de la scene a la scene principale 
        stage.show(); // Affichage de la scene dans l'app

        // Thread séparé pour écouter le serveur Python
//----------------------------------------------
        new Thread(
                this::listenToServer
        ).start();
    }

    // Mise en place de la fonction d'écoute du serveur
    private void listenToServer() {
        try (Socket socket = new Socket(HOST, PORT); // connection au port
            BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) { //mise en place du listener et reception
            System.out.println("✅ Connecté au serveur Python.");

            // conversion du fichier en json utilisable
            String line;
            while ((line = reader.readLine()) != null) {
                JSONObject worldData = new JSONObject(line);
            
            // Mise à jour des dimensions du monde
            double worldWidth = worldData.getDouble("width"); // récupération et conversion en int des dim de la carte
            double worldHeight = worldData.getDouble("height");
//----------------------------------------------
                Platform.runLater( () -> {
                    
                    root.getChildren().clear(); // suppression de tous les éléments de la grille

                    double scaleX = WIDTH / worldWidth;
                    double scaleY = HEIGHT / worldHeight;

                    // Boucle qui gère les ressources
                    JSONArray resources = worldData.getJSONArray("resources"); // réception de la liste des ressources
                    for (int i = 0; i < resources.length(); i++) { // Parcours de la liste
                        JSONObject r = resources.getJSONObject(i); // recuperation des obj a l'intérieur
                        double x = r.getDouble("x"); //conversion des coo en flottants
                        double y = r.getDouble("y");
                        String type = r.getString("type"); // conversion du type en string(water, grass)

                        if (type.equals("Water")) { // si c'est de l'eau
                            Rectangle water = new Rectangle((x * scaleX) - 4, (y * scaleY) - 4, 8, 8);
                            water.setFill(Color.web(water_color)); // On applique la couleur bleue
                            root.getChildren().add(water);
                        }
                        else if (type.equals("Grass")) { // si c'est de l'herbe
                            Rectangle grass = new Rectangle((x * scaleX) - 4, (y * scaleY) - 4, 8, 8);
                            grass.setFill(Color.valueOf(grass_color)); // On applique la couleur verte
                            root.getChildren().add(grass);
                        }
                    }

                    // Boucle qui gère les agents
                    JSONArray agents = worldData.getJSONArray("agents"); // recuperation de la liste des agents
                    for (int i = 0; i < agents.length(); i++) { // Parcours de cette liste 
                        JSONObject a = agents.getJSONObject(i); // recuperation de l'agent a la position i
                        double x = a.getDouble("x"); //conversion des coo en flottants
                        double y = a.getDouble("y");
                        String type = a.getString("type"); // conversion du type en string

                        Circle agentCircle; // mise en place du shape en cercle des agents

                        if (type.equals("Wolf")) { // si c'est un loup
                            // creation de l'agent avec son shape en cercle
                            agentCircle = new Circle(x*scaleX, y*scaleY, 5, Color.web(wolf_color));

                        }
                        else { // si c'est un mouton
                            // creation de l'agent avec son shape en cercle
                            agentCircle = new Circle(x*scaleX, y*scaleY, 6, Color.valueOf(sheep_color));
                            agentCircle.setStroke(Color.BLACK); // coloration den noir des contours de l'agent
                        }

                        root.getChildren().add(agentCircle); // Ajout du cercle au canevas
                    }
                });
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Lancement de la simulation
    static void main() {
        launch();
    }
}
