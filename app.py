from flask import Flask, send_from_directory, render_template, jsonify, request
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
MQTT_TOPICS = {
    "response": "response/#",  # Utilisation du wildcard MQTT pour capturer tous les sous-topics
    "door": "door"
}

# Variable globale pour stocker l'état du coffre-fort
safe_status = "closed"

# Stockage des logs en mémoire (limité aux 100 derniers)
activity_logs = deque(maxlen=100)

# Gestionnaire des messages MQTT
def on_mqtt_message(client, userdata, message):
    try:
        global safe_status
        payload = message.payload.decode().lower().strip()
        topic = message.topic
        
        print(f"Message MQTT reçu - Topic: {topic}, Payload: {payload}")  # Debug log
        
        # Messages du topic response/{mac_address}
        if topic.startswith(MQTT_TOPICS["response"].replace("/#", "/")):
            mac_address = topic.split('/')[-1]
            if payload == "allowed":
                status = "authorized"
                message_text = "Accès autorisé"
                safe_status = "authorized"
                badge_uid = None
            elif payload == "denied":
                status = "denied"
                message_text = "Accès refusé"
                safe_status = "denied"
                badge_uid = None
            elif payload == "close":
                status = "closed"
                message_text = "Porte fermée"
                safe_status = "closed"
                badge_uid = None
            elif payload.startswith("green"):
                status = "authorized"
                message_text = "Badge ajouté"
                safe_status = safe_status  # Ne pas changer l'état du coffre
                # Extraire l'UID du badge du message
                badge_uid = payload.split(" ")[1] if len(payload.split(" ")) > 1 else None
            else:
                return  # Ignorer les autres messages
        # Messages du topic door
        elif topic == MQTT_TOPICS["door"] and payload == "close":
            status = "closed"
            message_text = "Porte fermée"
            safe_status = "closed"
            badge_uid = None
            print("Fermeture du coffre détectée")  # Debug log
        else:
            print(f"Topic ignoré: {topic}")  # Debug log
            return  # Ignorer les autres messages/topics
        
        # Créer le message
        log_entry = {
            "type": "access_log",
            "message": message_text,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Ajouter l'UID du badge si présent
        if badge_uid:
            log_entry["badge_uid"] = badge_uid
        
        print(f"Log entry créé: {log_entry}")  # Debug log
        
        # Sauvegarder le log
        activity_logs.appendleft(log_entry)
        
        # Envoyer le message à tous les clients WebSocket connectés
        print(f"Nombre de clients WebSocket connectés: {len(connected_clients)}")  # Debug log
        for client in connected_clients.copy():
            try:
                message_json = json.dumps(log_entry)
                print(f"Envoi du message au client WebSocket: {message_json}")  # Debug log
                client.send(message_json)
            except Exception as e:
                print(f"Erreur lors de l'envoi au client WebSocket: {str(e)}")  # Debug log
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
for topic in MQTT_TOPICS.values():
    mqtt_client.subscribe(topic)
mqtt_client.loop_start()

# Gestionnaire WebSocket
@sock.route('/ws')
def handle_websocket(ws):
    print(f"Nouvelle connexion WebSocket établie")  # Debug log
    connected_clients.add(ws)
    print(f"Nombre total de clients connectés: {len(connected_clients)}")  # Debug log
    try:
        while True:
            message = ws.receive()
            print(f"Message WebSocket reçu: {message}")  # Debug log
    except Exception as e:
        print(f"Erreur WebSocket: {str(e)}")  # Debug log
    finally:
        connected_clients.remove(ws)
        print(f"Client WebSocket déconnecté. Restants: {len(connected_clients)}")  # Debug log

# Route pour obtenir l'état actuel du coffre-fort et les logs
@app.route('/api/safe-status')
def get_safe_status():
    return jsonify({
        "status": safe_status,
        "logs": list(activity_logs)  # Convertir deque en liste pour la sérialisation JSON
    })

# Route pour enregistrer un badge
@app.route('/api/badges', methods=['POST'])
def save_badge():
    try:
        data = request.json
        uid = data.get('uid')
        name = data.get('name')
        
        if not uid or not name:
            return jsonify({'error': 'UID et nom requis'}), 400
        
        badge = Badge(uid=uid, name=name)
        db.session.add(badge)
        db.session.commit()
        
        return jsonify(badge.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Importer les routes après avoir configuré l'application
from func.auth_routes import *
from func.badge_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables de la base de données vérifiées/créées.")
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)