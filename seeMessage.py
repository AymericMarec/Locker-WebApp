# Installation: pip install paho-mqtt
import paho.mqtt.client as mqtt
from datetime import datetime

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecté au broker MQTT avec code: {rc}")
    # S'abonner à tous les topics
    client.subscribe("#")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Abonné à tous les topics (#)")
    print(f"{'='*50}\n")

def on_message(client, userdata, msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] Nouveau message reçu:")
    print(f"Topic: {msg.topic}")
    print(f"Message: {msg.payload.decode()}")
    print(f"QoS: {msg.qos}")
    print(f"Retain: {'Oui' if msg.retain else 'Non'}")
    print("-" * 50)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Déconnexion inattendue du broker MQTT")
    else:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Déconnecté du broker MQTT")

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Abonnement réussi avec QoS: {granted_qos}")

# Création du client MQTT
client = mqtt.Client(protocol=mqtt.MQTTv5)

# Configuration des callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe

# Connexion au broker
try:
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tentative de connexion au broker MQTT...")
    client.connect("localhost", 1883, 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] En attente des messages...")
    print(f"{'='*50}\n")
    print("Appuyez sur Ctrl+C pour arrêter le programme\n")
    client.loop_forever()

except KeyboardInterrupt:
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Arrêt du programme...")
    client.disconnect()
    print(f"{'='*50}\n")

except Exception as e:
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur: {str(e)}")
    client.disconnect()
    print(f"{'='*50}\n")