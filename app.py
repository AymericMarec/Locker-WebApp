from flask import Flask, send_from_directory, render_template, jsonify
import os
from flask_sock import Sock
from extensions import db
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from collections import deque

app = Flask(__name__, 
            template_folder='templates')
app.secret_key = os.urandom(24)
sock = Sock(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://locker:root@localhost:3306/locker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Liste des clients WebSocket connectés
connected_clients = set()

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "response"

# Variable globale pour stocker l'état du coffre-fort
safe_status = "closed"

# Stockage des logs en mémoire (limité aux 100 derniers)
activity_logs = deque(maxlen=100)

# Gestionnaire des messages MQTT
def on_mqtt_message(client, userdata, message):
    try:
        global safe_status
        payload = message.payload.decode().lower().strip()
        
        # Éviter les messages en double
        if activity_logs and len(activity_logs) > 0:
            last_log = activity_logs[0]
            # Si le dernier message date de moins d'une seconde, on l'ignore
            if (datetime.now() - datetime.fromisoformat(last_log['timestamp'])).total_seconds() < 1:
                return

        if payload == "allowed":
            status = "authorized"
            message_text = "Accès autorisé"
            safe_status = "authorized"
        elif payload == "denied":
            status = "denied"
            message_text = "Accès refusé"
            safe_status = "denied"
        elif payload == "close":
            status = "closed"
            message_text = "Fermeture du coffre-fort"
            safe_status = "closed"
        elif payload == "green":
            status = "authorized"
            message_text = "Badge vert ajouté"
            safe_status = safe_status  # Ne pas changer l'état du coffre
        else:
            return  # Ignorer les autres messages
        
        # Créer le message
        log_entry = {
            "type": "access_log",
            "message": message_text,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Sauvegarder le log
        activity_logs.appendleft(log_entry)
        
        # Envoyer le message à tous les clients WebSocket connectés
        for client in connected_clients.copy():
            try:
                client.send(json.dumps(log_entry))
            except:
                connected_clients.remove(client)
    except Exception as e:
        print(f"Erreur lors du traitement du message MQTT: {str(e)}")

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)

# Configuration du client MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe(MQTT_TOPIC)
mqtt_client.loop_start()

# Gestionnaire WebSocket
@sock.route('/ws')
def handle_websocket(ws):
    connected_clients.add(ws)
    try:
        while True:
            message = ws.receive()
            # Gérer les messages entrants du client si nécessaire
    except:
        pass
    finally:
        connected_clients.remove(ws)

# Route pour obtenir l'état actuel du coffre-fort
@app.route('/api/safe-status')
def get_safe_status():
    return jsonify({
        "status": safe_status,
        "logs": list(activity_logs)  # Convertir deque en liste pour la sérialisation JSON
    })

# Importer les routes après avoir configuré l'application
from func.auth_routes import *
from func.badge_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables de la base de données vérifiées/créées.")
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)