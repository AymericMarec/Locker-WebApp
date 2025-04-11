from flask import Flask, send_from_directory, render_template, jsonify, request, session, redirect, url_for
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
pairing_clients = set()

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = {
    "response": "response/#",
    "door": "door",
    "pair": "pair"
}

# Variable globale pour stocker l'état du coffre-fort
safe_status = "closed"

# Stockage des logs en mémoire (limité aux 100 derniers)
activity_logs = deque(maxlen=100)

# Stockage des adresses MAC reçues
available_macs = set()

# Gestionnaire des messages MQTT
def on_mqtt_message(client, userdata, message):
    try:
        global safe_status
        payload = message.payload.decode().lower().strip()
        topic = message.topic
        
        print(f"Message MQTT reçu - Topic: {topic}, Payload: {payload}")
        
        # Messages du topic pair
        if topic == MQTT_TOPICS["pair"]:
            mac_address = payload
            available_macs.add(mac_address)
            # Envoyer la liste mise à jour à tous les clients d'appairage
            for client in pairing_clients.copy():
                try:
                    message_json = json.dumps({
                        "type": "mac_list",
                        "macs": list(available_macs)
                    })
                    client.send(message_json)
                except Exception as e:
                    print(f"Erreur lors de l'envoi au client d'appairage: {str(e)}")
                    pairing_clients.remove(client)
            return
        
        # Messages du topic response/{mac_address}
        if topic.startswith(MQTT_TOPICS["response"].replace("/#", "/")):
            mac_address = topic.split('/')[-1]
            # Vérifier si le message concerne un locker disponible
            if mac_address in available_macs:
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
                    safe_status = safe_status
                    badge_uid = payload.split(" ")[1] if len(payload.split(" ")) > 1 else None
                else:
                    return
            else:
                return  # Ignorer les messages des lockers non disponibles
        elif topic == MQTT_TOPICS["door"] and payload == "close":
            status = "closed"
            message_text = "Porte fermée"
            safe_status = "closed"
            badge_uid = None
            print("Fermeture du coffre détectée")
        else:
            print(f"Topic ignoré: {topic}")
            return
        
        log_entry = {
            "type": "access_log",
            "message": message_text,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if badge_uid:
            log_entry["badge_uid"] = badge_uid
        
        print(f"Log entry créé: {log_entry}")
        
        activity_logs.appendleft(log_entry)
        
        for client in connected_clients.copy():
            try:
                message_json = json.dumps(log_entry)
                print(f"Envoi du message au client WebSocket: {message_json}")
                client.send(message_json)
            except Exception as e:
                print(f"Erreur lors de l'envoi au client WebSocket: {str(e)}")
                connected_clients.remove(client)
    except Exception as e:
        print(f"Erreur lors du traitement du message MQTT: {str(e)}")

@app.route('/')
def index():
    if 'paired_mac' not in session:
        return redirect(url_for('pairing'))
    return render_template('index.html')

@app.route('/pairing')
def pairing():
    if 'paired_mac' in session:
        return redirect(url_for('index'))
    return render_template('pairing.html')

@app.route('/api/pair', methods=['POST'])
def pair_locker():
    data = request.json
    mac = data.get('mac')
    password = data.get('password')
    
    if not mac or not password:
        return jsonify({'success': False, 'message': 'Adresse MAC et mot de passe requis'})
    
    # Vérification du mot de passe
    if password == "admin123":  # À remplacer par votre logique d'authentification
        session['paired_mac'] = mac
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Mot de passe incorrect'})

@app.route('/logout')
def logout():
    session.pop('paired_mac', None)
    return redirect(url_for('pairing'))

@sock.route('/ws/pairing')
def handle_pairing_websocket(ws):
    print("Nouvelle connexion WebSocket d'appairage établie")
    pairing_clients.add(ws)
    
    # Envoyer la liste initiale des MACs
    try:
        message_json = json.dumps({
            "type": "mac_list",
            "macs": list(available_macs)
        })
        ws.send(message_json)
    except Exception as e:
        print(f"Erreur lors de l'envoi de la liste initiale: {str(e)}")
    
    try:
        while True:
            message = ws.receive()
            print(f"Message WebSocket d'appairage reçu: {message}")
    except Exception as e:
        print(f"Erreur WebSocket d'appairage: {str(e)}")
    finally:
        pairing_clients.remove(ws)
        print("Client WebSocket d'appairage déconnecté")

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
    print(f"Nouvelle connexion WebSocket établie")
    connected_clients.add(ws)
    print(f"Nombre total de clients connectés: {len(connected_clients)}")
    try:
        while True:
            message = ws.receive()
            print(f"Message WebSocket reçu: {message}")
    except Exception as e:
        print(f"Erreur WebSocket: {str(e)}")
    finally:
        connected_clients.remove(ws)
        print(f"Client WebSocket déconnecté. Restants: {len(connected_clients)}")

# Route pour obtenir l'état actuel du coffre-fort et les logs
@app.route('/api/safe-status')
def get_safe_status():
    if 'paired_mac' not in session:
        return jsonify({'error': 'Non appairé'}), 401
    return jsonify({
        "status": safe_status,
        "logs": list(activity_logs)
    })

# Route pour enregistrer un badge
@app.route('/api/badges', methods=['POST'])
def save_badge():
    if 'paired_mac' not in session:
        return jsonify({'error': 'Non appairé'}), 401
        
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
from func.badge_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables de la base de données vérifiées/créées.")
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)