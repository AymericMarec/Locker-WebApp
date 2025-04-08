import paho.mqtt.client as mqtt
import json
import time
from app import app
from models.badge import Badge
from extensions import db

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_SCAN = "scan"
MQTT_TOPIC_RESPONSE = "response"

# Variables globales
last_scan = None
last_scan_time = 0
last_processed_payload = None
last_processed_time = 0

def on_connect(client, userdata, flags, rc):
    print("Connecté au broker MQTT")
    client.subscribe(MQTT_TOPIC_SCAN)

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
        
        if msg.topic == MQTT_TOPIC_SCAN:
            # Utiliser directement le payload comme UID
            uid = payload
            last_scan = uid
            last_scan_time = time.time()
            print(f"Badge scanné: {uid}")
            
            # Vérifier l'autorisation du badge
            with app.app_context():
                badge = Badge.query.filter_by(uid=uid).first()
                is_authorized = badge.is_authorized if badge else False
                
                # Publier une réponse sur le topic response
                response = "true" if is_authorized else "false"
                client.publish(MQTT_TOPIC_RESPONSE, response, qos=1)
                print(f"Réponse envoyée sur {MQTT_TOPIC_RESPONSE}: {response}")
            
    except Exception as e:
        print(f"Erreur lors du traitement du message: {e}")

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
    
    # Si le dernier scan date de plus de 5 secondes, on le considère comme expiré
    if current_time - last_scan_time > 5:
        last_scan = None
    
    return last_scan 