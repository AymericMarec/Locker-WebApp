import paho.mqtt.client as mqtt
import json
import time
from app import app
from models.badge import Badge
from extensions import db

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_SCAN = "scan"
MQTT_TOPIC_DOOR = "door"
MQTT_TOPIC_RESPONSE = "response"
MQTT_MSG_CLOSE = "close"
MQTT_MSG_ALLOWED = "allowed"
MQTT_MSG_DENIED = "denied"

last_scan = None
last_scan_time = 0
last_processed_payload = None
last_processed_time = 0
is_adding_badge = False  

def on_connect(client, userdata, flags, rc):
    print("Connecté au broker MQTT")
    client.subscribe(MQTT_TOPIC_SCAN)
    client.subscribe(MQTT_TOPIC_DOOR)

def on_message(client, userdata, msg):
    global last_scan, last_scan_time, last_processed_payload, last_processed_time
    
    try:
        payload = msg.payload.decode()
        current_time = time.time()
        
        # Réinitialiser last_processed_payload après 2 secondes
        if current_time - last_processed_time > 2:
            last_processed_payload = None
        
        # Ignorer les messages dupliqués
        if payload == last_processed_payload:
            return
            
        last_processed_payload = payload
        last_processed_time = current_time
        
        if msg.topic == MQTT_TOPIC_DOOR:
            if payload == MQTT_MSG_CLOSE:
                print("Commande de fermeture de porte reçue")
                return

        if msg.topic == MQTT_TOPIC_SCAN:
      
            mac_address = payload.split('|')[0]
            uid = payload.split('|')[1]
            response_topic = f"{MQTT_TOPIC_RESPONSE}/{mac_address}"
            
            last_scan = uid
            last_scan_time = time.time()
            print(f"Badge scanné: {payload}")
            
            with app.app_context():
                badge = Badge.query.filter_by(uid=uid).first()
                
                if not badge:
                    if is_adding_badge:
                        # Si on est en mode ajout de badge, on l'ajoute à la base de données
                        try:
                            new_badge = Badge(uid=uid, name="Badge scanné", is_authorized=True)
                            db.session.add(new_badge)
                            db.session.commit()
                            print(f"Nouveau badge ajouté à la DB: {uid}")
                            response = MQTT_MSG_ALLOWED  # Envoyer allowed après l'ajout réussi
                            client.publish(response_topic, response, qos=1)
                            print(f"Réponse envoyée sur {response_topic}: {response}")
                        except Exception as e:
                            print(f"Erreur lors de l'ajout du badge: {e}")
                            db.session.rollback()
                            response = MQTT_MSG_DENIED
                            client.publish(response_topic, response, qos=1)
                            print(f"Réponse envoyée sur {response_topic}: {response}")
                    else:
                        # Si on n'est pas en mode ajout, on refuse l'accès
                        response = MQTT_MSG_DENIED
                        client.publish(response_topic, response, qos=1)
                        print(f"Badge inconnu, accès refusé: {uid}")
                else:
                    # Si le badge existe, vérifier son autorisation
                    response = MQTT_MSG_ALLOWED if badge.is_authorized else MQTT_MSG_DENIED
                    client.publish(response_topic, response, qos=1)
                    print(f"Réponse envoyée sur {response_topic}: {response}")
            
    except Exception as e:
        print(f"Erreur lors du traitement du message: {e}")
        if 'db' in locals():
            db.session.rollback()

def init_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        return client
    except Exception as e:
        print(f"Erreur de connexion MQTT: {e}")
        return None

def get_last_scan():
    global last_scan, last_scan_time
    current_time = time.time()
    
    if current_time - last_scan_time > 5:
        last_scan = None
    
    return last_scan 

def set_adding_badge_mode(enabled):
    global is_adding_badge
    is_adding_badge = enabled
    print(f"Mode ajout de badge: {'activé' if enabled else 'désactivé'}") 