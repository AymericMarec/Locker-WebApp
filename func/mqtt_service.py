import paho.mqtt.client as mqtt
from func.mqtt_config import *
import datetime

websocket_clients = set()

last_scan = None

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"\n{'='*50}")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecté au broker MQTT avec code: {rc}")
    client.subscribe(MQTT_TOPIC_SCAN)
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Abonné au topic '{MQTT_TOPIC_SCAN}'")
    print(f"{'='*50}\n")

def on_message(client, userdata, msg):
    from app import app
    from models.badge import Badge
    
    global last_scan
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Message reçu - Topic: {topic}, Payload: {payload}")

    if topic == MQTT_TOPIC_SCAN:
        last_scan = payload
        with app.app_context():
            badge = Badge.query.filter_by(uid=payload).first()
            if badge and badge.is_authorized:
                print(f"Badge {payload} autorisé. Envoi de 'true' sur 'response'")
                client.publish(MQTT_TOPIC_RESPONSE, "true")
            else:
                print(f"Badge {payload} non trouvé ou non autorisé. Envoi de 'false' sur 'response'")
                client.publish(MQTT_TOPIC_RESPONSE, "false")

def init_mqtt_client():
    mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    return mqtt_client 